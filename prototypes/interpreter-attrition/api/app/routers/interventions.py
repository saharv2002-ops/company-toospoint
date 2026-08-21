"""GET + POST /api/interventions — dedicated intervention log endpoints
(separate from /api/ingest/interventions which is for bulk backfill)."""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Interpreter, Intervention
from app.schemas.reads import (
    InterventionCreate,
    InterventionListItem,
    InterventionListResponse,
    InterventionRead,
)

router = APIRouter(prefix="/api/interventions", tags=["interventions"])


@router.get("", response_model=InterventionListResponse)
def list_interventions(
    interpreter_id: UUID | None = None,
    action: str | None = None,
    outcome: str | None = None,
    since_days: int | None = Query(default=None, ge=1, le=365),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> InterventionListResponse:
    stmt = select(
        Intervention.id,
        Intervention.interpreter_id,
        Intervention.action,
        Intervention.notes,
        Intervention.created_at,
        Intervention.outcome,
        Interpreter.full_name,
        Interpreter.external_id,
    ).join(Interpreter, Interpreter.id == Intervention.interpreter_id)

    filters = []
    if interpreter_id is not None:
        filters.append(Intervention.interpreter_id == interpreter_id)
    if action is not None:
        filters.append(Intervention.action == action)
    if outcome is not None:
        filters.append(Intervention.outcome == outcome)
    if since_days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
        filters.append(Intervention.created_at >= cutoff)
    if filters:
        stmt = stmt.where(*filters)

    total = db.execute(
        select(func.count()).select_from(stmt.order_by(None).subquery())
    ).scalar_one()

    stmt = stmt.order_by(Intervention.created_at.desc()).limit(limit).offset(offset)
    rows = db.execute(stmt).all()
    items = [
        InterventionListItem(
            id=row.id,
            interpreter_id=row.interpreter_id,
            interpreter_name=row.full_name,
            interpreter_external_id=row.external_id,
            action=row.action,
            notes=row.notes,
            created_at=row.created_at,
            outcome=row.outcome,
        )
        for row in rows
    ]
    return InterventionListResponse(items=items, total=int(total), limit=limit, offset=offset)


@router.post("", response_model=InterventionRead, status_code=201)
def create_intervention(
    payload: InterventionCreate, db: Session = Depends(get_db)
) -> InterventionRead:
    exists = db.execute(
        select(Interpreter.id).where(Interpreter.id == payload.interpreter_id)
    ).scalar_one_or_none()
    if exists is None:
        raise HTTPException(status_code=400, detail="unknown_interpreter_id")
    row = Intervention(
        interpreter_id=payload.interpreter_id,
        action=payload.action,
        notes=payload.notes,
        outcome=payload.outcome,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return InterventionRead.model_validate(row)
