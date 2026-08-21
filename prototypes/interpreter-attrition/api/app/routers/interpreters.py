"""Read endpoints for the interpreter roster.

- GET /api/interpreters        — filterable, paginated list
- GET /api/interpreters/{id}   — profile + latest score + signal readouts
- GET /api/interpreters/{id}/timeline?days=90 — daily signal history for sparklines
"""
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.enums import ChurnBand, InterpreterStatus
from app.models import ChurnScore, Feedback, Interpreter, Intervention
from app.models import Session as SessionModel
from app.schemas.reads import (
    InterpreterDetail,
    InterpreterListItem,
    InterpreterListResponse,
    LatestScore,
    SignalReadout,
    TimelinePoint,
    TimelineResponse,
)
from app.services.explanations import SIGNAL_NAMES, explain_signal
from app.services.scoring import FEEDBACK_WINDOW_DAYS, WEIGHTS, SignalInputs

router = APIRouter(prefix="/api/interpreters", tags=["interpreters"])


def _tenure_days(hired_at: date, today: date) -> int:
    return (today - hired_at).days


def _latest_score_for(db: Session, interpreter_id: UUID) -> ChurnScore | None:
    return db.execute(
        select(ChurnScore)
        .where(ChurnScore.interpreter_id == interpreter_id)
        .order_by(ChurnScore.as_of.desc())
        .limit(1)
    ).scalar_one_or_none()


def _last_session_at(db: Session, interpreter_id: UUID) -> datetime | None:
    return db.execute(
        select(func.max(SessionModel.started_at)).where(
            SessionModel.interpreter_id == interpreter_id
        )
    ).scalar_one_or_none()


def _top_signal_key(score: ChurnScore) -> int:
    """Return the signal number (1-6) with the highest weighted contribution."""
    contributions = {
        1: score.signal_1_volume * WEIGHTS[1],
        2: score.signal_2_decline * WEIGHTS[2],
        3: score.signal_3_latency * WEIGHTS[3],
        4: score.signal_4_feedback * WEIGHTS[4],
        5: score.signal_5_tenure * WEIGHTS[5],
        6: score.signal_6_availability * WEIGHTS[6],
    }
    return max(contributions, key=contributions.get)


@router.get("", response_model=InterpreterListResponse)
def list_interpreters(
    band: ChurnBand | None = None,
    language: str | None = Query(default=None, min_length=2, max_length=8),
    min_tenure_days: int | None = Query(default=None, ge=0),
    max_days_since_last_session: int | None = Query(default=None, ge=0),
    status: InterpreterStatus | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> InterpreterListResponse:
    today = datetime.now(timezone.utc).date()

    # Latest score per interpreter (correlated subquery via DISTINCT ON — Postgres)
    latest = (
        select(
            ChurnScore.interpreter_id,
            ChurnScore.as_of,
            ChurnScore.composite_score,
            ChurnScore.band,
            ChurnScore.signal_1_volume,
            ChurnScore.signal_2_decline,
            ChurnScore.signal_3_latency,
            ChurnScore.signal_4_feedback,
            ChurnScore.signal_5_tenure,
            ChurnScore.signal_6_availability,
        )
        .distinct(ChurnScore.interpreter_id)
        .order_by(ChurnScore.interpreter_id, ChurnScore.as_of.desc())
        .subquery()
    )

    last_session = (
        select(
            SessionModel.interpreter_id,
            func.max(SessionModel.started_at).label("last_at"),
        )
        .group_by(SessionModel.interpreter_id)
        .subquery()
    )

    stmt = (
        select(
            Interpreter,
            latest.c.as_of,
            latest.c.composite_score,
            latest.c.band,
            latest.c.signal_1_volume,
            latest.c.signal_2_decline,
            latest.c.signal_3_latency,
            latest.c.signal_4_feedback,
            latest.c.signal_5_tenure,
            latest.c.signal_6_availability,
            last_session.c.last_at,
        )
        .join(latest, latest.c.interpreter_id == Interpreter.id, isouter=True)
        .join(last_session, last_session.c.interpreter_id == Interpreter.id, isouter=True)
    )

    filters = []
    if band is not None:
        filters.append(latest.c.band == band.value)
    if language is not None:
        filters.append(Interpreter.languages.any(language))
    if min_tenure_days is not None:
        filters.append(Interpreter.hired_at <= today - timedelta(days=min_tenure_days))
    if status is not None:
        filters.append(Interpreter.status == status)
    if max_days_since_last_session is not None:
        cutoff = datetime.combine(
            today - timedelta(days=max_days_since_last_session),
            datetime.min.time(),
            tzinfo=timezone.utc,
        )
        filters.append(last_session.c.last_at >= cutoff)

    if filters:
        stmt = stmt.where(*filters)

    total = db.execute(
        select(func.count()).select_from(stmt.order_by(None).subquery())
    ).scalar_one()

    stmt = stmt.order_by(latest.c.composite_score.desc().nulls_last()).limit(limit).offset(offset)
    rows = db.execute(stmt).all()

    items: list[InterpreterListItem] = []
    for (
        interp, as_of, composite, band_val,
        s1, s2, s3, s4, s5, s6,
        last_at,
    ) in rows:
        latest_score: LatestScore | None = None
        if as_of is not None:
            fake_score = ChurnScore(
                interpreter_id=interp.id,
                as_of=as_of,
                composite_score=composite,
                signal_1_volume=s1,
                signal_2_decline=s2,
                signal_3_latency=s3,
                signal_4_feedback=s4,
                signal_5_tenure=s5,
                signal_6_availability=s6,
                band=ChurnBand(band_val),
            )
            latest_score = LatestScore(
                as_of=as_of,
                composite_score=composite,
                band=ChurnBand(band_val),
                top_signal_key=_top_signal_key(fake_score),
            )
        items.append(
            InterpreterListItem(
                id=interp.id,
                external_id=interp.external_id,
                full_name=interp.full_name,
                languages=list(interp.languages),
                tenure_days=_tenure_days(interp.hired_at, today),
                status=interp.status,
                latest_score=latest_score,
                last_session_at=last_at,
            )
        )

    return InterpreterListResponse(items=items, total=int(total), limit=limit, offset=offset)


def _build_signal_inputs_for(db: Session, interpreter_id: UUID, as_of: date) -> SignalInputs:
    """Rebuild SignalInputs from the DB for a single interpreter.

    Used by the detail endpoint so it can emit fresh "why" copy tied to
    the actual data behind the latest score.
    """
    from app.services.scoring import collect_all_inputs

    for inp in collect_all_inputs(db, as_of):
        if inp.interpreter_id == interpreter_id:
            return inp
    # If we asked for an interpreter that no aggregate touched, return a
    # zeroed input tied to their hired_at so the tenure signal still works.
    hired = db.execute(
        select(Interpreter.hired_at).where(Interpreter.id == interpreter_id)
    ).scalar_one()
    return SignalInputs(interpreter_id=interpreter_id, hired_at=hired)


@router.get("/{interpreter_id}", response_model=InterpreterDetail)
def get_interpreter(interpreter_id: UUID, db: Session = Depends(get_db)) -> InterpreterDetail:
    interp = db.execute(
        select(Interpreter).where(Interpreter.id == interpreter_id)
    ).scalar_one_or_none()
    if interp is None:
        raise HTTPException(status_code=404, detail="interpreter_not_found")

    today = datetime.now(timezone.utc).date()
    latest = _latest_score_for(db, interpreter_id)

    latest_score: LatestScore | None = None
    signals: list[SignalReadout] = []
    if latest is not None:
        latest_score = LatestScore(
            as_of=latest.as_of,
            composite_score=latest.composite_score,
            band=latest.band,
            top_signal_key=_top_signal_key(latest),
        )
        inp = _build_signal_inputs_for(db, interpreter_id, latest.as_of)
        signal_scores = {
            1: latest.signal_1_volume,
            2: latest.signal_2_decline,
            3: latest.signal_3_latency,
            4: latest.signal_4_feedback,
            5: latest.signal_5_tenure,
            6: latest.signal_6_availability,
        }
        for key in range(1, 7):
            signals.append(
                SignalReadout(
                    key=key,
                    name=SIGNAL_NAMES[key],
                    score=signal_scores[key],
                    weight=WEIGHTS[key],
                    why=explain_signal(key, inp, latest.as_of),
                )
            )

    intervention_count = db.execute(
        select(func.count()).select_from(Intervention).where(
            Intervention.interpreter_id == interpreter_id,
            Intervention.created_at
            >= datetime.now(timezone.utc) - timedelta(days=FEEDBACK_WINDOW_DAYS),
        )
    ).scalar_one()

    return InterpreterDetail(
        id=interp.id,
        external_id=interp.external_id,
        full_name=interp.full_name,
        languages=list(interp.languages),
        certifications=list(interp.certifications),
        hired_at=interp.hired_at,
        tenure_days=_tenure_days(interp.hired_at, today),
        status=interp.status,
        home_timezone=interp.home_timezone,
        latest_score=latest_score,
        signals=signals,
        last_session_at=_last_session_at(db, interpreter_id),
        recent_intervention_count=int(intervention_count),
    )


@router.get("/{interpreter_id}/timeline", response_model=TimelineResponse)
def get_timeline(
    interpreter_id: UUID,
    days: int = Query(default=30, ge=1, le=90),
    db: Session = Depends(get_db),
) -> TimelineResponse:
    exists = db.execute(
        select(Interpreter.id).where(Interpreter.id == interpreter_id)
    ).scalar_one_or_none()
    if exists is None:
        raise HTTPException(status_code=404, detail="interpreter_not_found")

    cutoff = datetime.now(timezone.utc).date() - timedelta(days=days)
    rows = db.execute(
        select(ChurnScore)
        .where(ChurnScore.interpreter_id == interpreter_id, ChurnScore.as_of >= cutoff)
        .order_by(ChurnScore.as_of)
    ).scalars().all()
    points = [
        TimelinePoint(
            as_of=r.as_of,
            composite_score=r.composite_score,
            signal_1_volume=r.signal_1_volume,
            signal_2_decline=r.signal_2_decline,
            signal_3_latency=r.signal_3_latency,
            signal_4_feedback=r.signal_4_feedback,
            signal_5_tenure=r.signal_5_tenure,
            signal_6_availability=r.signal_6_availability,
        )
        for r in rows
    ]
    return TimelineResponse(interpreter_id=interpreter_id, days=days, points=points)
