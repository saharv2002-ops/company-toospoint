from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.scoring import MAX_BACKFILL_DAYS, recompute_all, recompute_range

router = APIRouter(prefix="/api/scores", tags=["scores"])


class RecomputeResponse(BaseModel):
    as_of: date
    scored: int
    band_counts: dict[str, int]


class BackfillResponse(BaseModel):
    end: date
    days: int
    total_scored: int


@router.post("/recompute", response_model=RecomputeResponse)
def recompute(as_of: date | None = None, db: Session = Depends(get_db)) -> RecomputeResponse:
    """Recompute churn scores for the entire roster as of the given date.

    Defaults to today (UTC) when as_of is omitted. Idempotent — re-running
    for the same as_of upserts each interpreter's score row.
    """
    target = as_of or datetime.now(timezone.utc).date()
    result = recompute_all(db, target)
    return RecomputeResponse(
        as_of=result.as_of, scored=result.scored, band_counts=result.band_counts
    )


@router.post("/backfill", response_model=BackfillResponse)
def backfill(
    days: int = Query(30, ge=1, le=MAX_BACKFILL_DAYS),
    end: date | None = None,
    db: Session = Depends(get_db),
) -> BackfillResponse:
    """Recompute scores for each of the last `days` days ending at `end`.

    Powers the 90-day sparklines on the interpreter detail screen. Idempotent.
    Defaults `end` to today (UTC) and `days` to 30.
    """
    target_end = end or datetime.now(timezone.utc).date()
    try:
        results = recompute_range(db, target_end, days)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return BackfillResponse(end=target_end, days=days, total_scored=sum(r.scored for r in results))
