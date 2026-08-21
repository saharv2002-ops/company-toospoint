"""Bulk-ingest endpoints for LSP data.

Each endpoint accepts an `IngestBatch[…]` and upserts via
Postgres `INSERT … ON CONFLICT DO UPDATE`. Idempotent by design —
re-posting the same batch is a no-op.
"""
from collections.abc import Sequence
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import (
    AvailabilitySnapshot,
    Dispatch,
    Feedback,
    Interpreter,
    Intervention,
)
from app.models import Session as SessionModel
from app.schemas import (
    AvailabilitySnapshotIngest,
    DispatchIngest,
    FeedbackIngest,
    IngestBatch,
    IngestResult,
    InterpreterIngest,
    SessionIngest,
)
from app.schemas.ingest import InterventionIngest

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


def _resolve_interpreter_ids(
    db: Session, external_ids: Sequence[str]
) -> dict[str, Any]:
    if not external_ids:
        return {}
    rows = db.execute(
        select(Interpreter.external_id, Interpreter.id).where(
            Interpreter.external_id.in_(list(set(external_ids)))
        )
    ).all()
    return {external_id: row_id for external_id, row_id in rows}


def _run_upsert(
    db: Session, table_model, rows: list[dict[str, Any]], index_elements: list[str]
) -> IngestResult:
    if not rows:
        return IngestResult(inserted=0, updated=0, total=0)

    stmt = pg_insert(table_model).values(rows)
    update_cols = {c.name: stmt.excluded[c.name] for c in table_model.__table__.columns if c.name not in index_elements}
    if update_cols:
        stmt = stmt.on_conflict_do_update(index_elements=index_elements, set_=update_cols)
    else:
        stmt = stmt.on_conflict_do_nothing(index_elements=index_elements)

    stmt = stmt.returning((table_model.__table__.c[index_elements[0]]))
    result = db.execute(stmt)
    returned = result.scalars().all()
    db.commit()
    # We can't cheaply distinguish insert vs update per-row without more work.
    # Report totals; refine in a later day if a prospect asks.
    return IngestResult(inserted=len(returned), updated=len(rows) - len(returned), total=len(rows))


@router.post("/interpreters", response_model=IngestResult)
def ingest_interpreters(
    batch: IngestBatch[InterpreterIngest], db: Session = Depends(get_db)
) -> IngestResult:
    rows = [item.model_dump() for item in batch.items]
    return _run_upsert(db, Interpreter, rows, index_elements=["external_id"])


def _rows_with_interpreter_fk(
    db: Session, items: list[Any]
) -> list[dict[str, Any]]:
    external_ids = [item.interpreter_external_id for item in items]
    mapping = _resolve_interpreter_ids(db, external_ids)
    missing = sorted({eid for eid in external_ids if eid not in mapping})
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "unknown_interpreter_external_ids", "missing": missing[:20]},
        )
    rows: list[dict[str, Any]] = []
    for item in items:
        payload = item.model_dump()
        payload["interpreter_id"] = mapping[payload.pop("interpreter_external_id")]
        rows.append(payload)
    return rows


@router.post("/sessions", response_model=IngestResult)
def ingest_sessions(
    batch: IngestBatch[SessionIngest], db: Session = Depends(get_db)
) -> IngestResult:
    rows = _rows_with_interpreter_fk(db, batch.items)
    return _run_upsert(db, SessionModel, rows, index_elements=["id"])


@router.post("/dispatches", response_model=IngestResult)
def ingest_dispatches(
    batch: IngestBatch[DispatchIngest], db: Session = Depends(get_db)
) -> IngestResult:
    rows = _rows_with_interpreter_fk(db, batch.items)
    return _run_upsert(db, Dispatch, rows, index_elements=["id"])


@router.post("/feedback", response_model=IngestResult)
def ingest_feedback(
    batch: IngestBatch[FeedbackIngest], db: Session = Depends(get_db)
) -> IngestResult:
    rows = [item.model_dump() for item in batch.items]
    return _run_upsert(db, Feedback, rows, index_elements=["id"])


@router.post("/availability", response_model=IngestResult)
def ingest_availability(
    batch: IngestBatch[AvailabilitySnapshotIngest], db: Session = Depends(get_db)
) -> IngestResult:
    rows = _rows_with_interpreter_fk(db, batch.items)
    return _run_upsert(
        db, AvailabilitySnapshot, rows, index_elements=["interpreter_id", "week_of"]
    )


@router.post("/interventions", response_model=IngestResult)
def ingest_interventions(
    batch: IngestBatch[InterventionIngest], db: Session = Depends(get_db)
) -> IngestResult:
    # Interventions don't have a natural unique key beyond id (which the DB
    # generates), so this endpoint inserts only. Bulk-updating past
    # interventions is out of scope for v1.
    rows = _rows_with_interpreter_fk(db, batch.items)
    if not rows:
        return IngestResult(inserted=0, updated=0, total=0)
    db.execute(pg_insert(Intervention).values(rows))
    db.commit()
    return IngestResult(inserted=len(rows), updated=0, total=len(rows))
