"""End-to-end: seed → recompute → verify band distribution.

Verifies the whole pipeline: seeded behaviour curves produce inputs
that the blind scoring engine places back into the same buckets
within the SPEC-required tolerance.
"""
from datetime import date

import pytest
from sqlalchemy import func, select

from app.models import ChurnScore
from app.services.scoring import recompute_all
from scripts.seed import generate, insert_all
from tests.conftest import requires_postgres

pytestmark = requires_postgres

SEED_TARGET_RED = 12
SEED_TARGET_YELLOW = 22
SEED_TARGET_GREEN = 66
TOLERANCE_PCT_POINTS = 3


@pytest.fixture(scope="module")
def seeded_engine(engine):
    """Seed the DB once for the whole scoring-e2e module."""
    today = date(2026, 8, 21)
    data = generate(seed=42, total=200, today=today)
    insert_all(
        engine,
        data["roster"],
        data["sessions"],
        data["dispatches"],
        data["feedback"],
        data["availability"],
        reset=True,
    )
    return engine


def test_recompute_lands_within_tolerance(seeded_engine, db):
    result = recompute_all(db, as_of=date(2026, 8, 21))
    assert result.scored == 200
    total = result.scored
    for band, target in (
        ("red", SEED_TARGET_RED),
        ("yellow", SEED_TARGET_YELLOW),
        ("green", SEED_TARGET_GREEN),
    ):
        actual_pct = result.band_counts[band] / total * 100
        assert abs(actual_pct - target) <= TOLERANCE_PCT_POINTS, (
            band, actual_pct, target
        )


def test_recompute_writes_churn_scores_table(seeded_engine, db):
    recompute_all(db, as_of=date(2026, 8, 21))
    row_count = db.execute(select(func.count()).select_from(ChurnScore)).scalar_one()
    assert row_count == 200


def test_recompute_is_idempotent(seeded_engine, db):
    recompute_all(db, as_of=date(2026, 8, 21))
    first_count = db.execute(select(func.count()).select_from(ChurnScore)).scalar_one()
    recompute_all(db, as_of=date(2026, 8, 21))
    second_count = db.execute(select(func.count()).select_from(ChurnScore)).scalar_one()
    assert first_count == second_count == 200


def test_recompute_endpoint(seeded_engine, client):
    r = client.post("/api/scores/recompute?as_of=2026-08-21")
    assert r.status_code == 200
    body = r.json()
    assert body["as_of"] == "2026-08-21"
    assert body["scored"] == 200
    total = body["scored"]
    for band, target in (
        ("red", SEED_TARGET_RED),
        ("yellow", SEED_TARGET_YELLOW),
        ("green", SEED_TARGET_GREEN),
    ):
        actual = body["band_counts"][band] / total * 100
        assert abs(actual - target) <= TOLERANCE_PCT_POINTS, (band, actual, target)
