from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.scoring import recompute_all

router = APIRouter(prefix="/api/scores", tags=["scores"])


class RecomputeResponse(BaseModel):
    as_of: date
    scored: int
    band_counts: dict[str, int]


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
