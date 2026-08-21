"""GET /api/dashboard/summary — the number the ops manager opens on Monday."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.enums import ChurnBand, InterpreterStatus
from app.models import ChurnScore, Interpreter
from app.schemas.reads import DashboardSummary, TopAtRisk

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db)) -> DashboardSummary:
    total_active = db.execute(
        select(func.count())
        .select_from(Interpreter)
        .where(Interpreter.status == InterpreterStatus.active)
    ).scalar_one()

    latest_as_of = db.execute(select(func.max(ChurnScore.as_of))).scalar_one()
    if latest_as_of is None:
        return DashboardSummary(
            as_of=datetime.now(timezone.utc).date(),
            total_active=int(total_active),
            band_counts={"red": 0, "yellow": 0, "green": 0},
            week_over_week={"red_delta": 0, "yellow_delta": 0, "green_delta": 0},
            top_at_risk=[],
        )

    band_counts = {"red": 0, "yellow": 0, "green": 0}
    for band, n in db.execute(
        select(ChurnScore.band, func.count())
        .where(ChurnScore.as_of == latest_as_of)
        .group_by(ChurnScore.band)
    ).all():
        band_counts[band.value] = int(n)

    week_ago = latest_as_of - timedelta(days=7)
    prior_counts = {"red": 0, "yellow": 0, "green": 0}
    for band, n in db.execute(
        select(ChurnScore.band, func.count())
        .where(ChurnScore.as_of == week_ago)
        .group_by(ChurnScore.band)
    ).all():
        prior_counts[band.value] = int(n)

    week_over_week = {
        "red_delta": band_counts["red"] - prior_counts["red"],
        "yellow_delta": band_counts["yellow"] - prior_counts["yellow"],
        "green_delta": band_counts["green"] - prior_counts["green"],
    }

    top_rows = db.execute(
        select(Interpreter, ChurnScore)
        .join(ChurnScore, ChurnScore.interpreter_id == Interpreter.id)
        .where(ChurnScore.as_of == latest_as_of)
        .order_by(ChurnScore.composite_score.desc())
        .limit(5)
    ).all()
    top_at_risk = [
        TopAtRisk(
            id=interp.id,
            external_id=interp.external_id,
            full_name=interp.full_name,
            languages=list(interp.languages),
            composite_score=score.composite_score,
            band=score.band,
        )
        for interp, score in top_rows
    ]

    return DashboardSummary(
        as_of=latest_as_of,
        total_active=int(total_active),
        band_counts=band_counts,
        week_over_week=week_over_week,
        top_at_risk=top_at_risk,
    )
