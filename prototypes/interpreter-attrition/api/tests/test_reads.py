"""Integration tests for the read endpoints against a seeded + backfilled DB."""
from datetime import date

import pytest
from sqlalchemy import select

from app.enums import InterventionAction
from app.models import Interpreter
from app.services.scoring import recompute_range
from scripts.seed import generate, insert_all
from tests.conftest import requires_postgres

pytestmark = requires_postgres

AS_OF = date(2026, 8, 21)


@pytest.fixture(scope="module")
def seeded_and_scored(engine):
    data = generate(seed=42, total=200, today=AS_OF)
    insert_all(
        engine,
        data["roster"],
        data["sessions"],
        data["dispatches"],
        data["feedback"],
        data["availability"],
        reset=True,
    )
    from sqlalchemy.orm import Session as ORMSession
    with ORMSession(engine) as db:
        recompute_range(db, AS_OF, days=14)  # enough for timeline + w-o-w
    return engine


def test_list_returns_all_seeded(seeded_and_scored, client):
    r = client.get("/api/interpreters?limit=500")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 200
    assert len(body["items"]) == 200
    first = body["items"][0]
    assert first["latest_score"] is not None
    assert first["latest_score"]["band"] in ("red", "yellow", "green")


def test_list_filter_by_band(seeded_and_scored, client):
    r_all = client.get("/api/interpreters?limit=500").json()
    r_red = client.get("/api/interpreters?band=red&limit=500").json()
    r_green = client.get("/api/interpreters?band=green&limit=500").json()
    assert r_red["total"] + r_green["total"] < r_all["total"]
    assert all(i["latest_score"]["band"] == "red" for i in r_red["items"])
    assert all(i["latest_score"]["band"] == "green" for i in r_green["items"])


def test_list_filter_by_language(seeded_and_scored, client):
    r = client.get("/api/interpreters?language=es&limit=500")
    assert r.status_code == 200
    for item in r.json()["items"]:
        assert "es" in item["languages"]


def test_list_pagination(seeded_and_scored, client):
    r1 = client.get("/api/interpreters?limit=25&offset=0").json()
    r2 = client.get("/api/interpreters?limit=25&offset=25").json()
    assert len(r1["items"]) == 25
    assert len(r2["items"]) == 25
    ids1 = {i["id"] for i in r1["items"]}
    ids2 = {i["id"] for i in r2["items"]}
    assert ids1.isdisjoint(ids2)


def test_interpreter_detail(seeded_and_scored, client, db):
    interp_id = db.execute(select(Interpreter.id).limit(1)).scalar_one()
    r = client.get(f"/api/interpreters/{interp_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == str(interp_id)
    assert len(body["signals"]) == 6
    for signal in body["signals"]:
        assert 1 <= signal["key"] <= 6
        assert isinstance(signal["why"], str) and len(signal["why"]) > 0
        assert signal["name"]
    assert body["latest_score"]["band"] in ("red", "yellow", "green")


def test_interpreter_detail_not_found(seeded_and_scored, client):
    r = client.get("/api/interpreters/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_timeline(seeded_and_scored, client, db):
    interp_id = db.execute(select(Interpreter.id).limit(1)).scalar_one()
    r = client.get(f"/api/interpreters/{interp_id}/timeline?days=14")
    assert r.status_code == 200
    body = r.json()
    assert body["days"] == 14
    # Backfilled 14 days of scores
    assert len(body["points"]) == 14
    assert body["points"][0]["as_of"] < body["points"][-1]["as_of"]


def test_dashboard_summary(seeded_and_scored, client):
    r = client.get("/api/dashboard/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["total_active"] == 200
    assert sum(body["band_counts"].values()) == 200
    assert set(body["week_over_week"].keys()) == {"red_delta", "yellow_delta", "green_delta"}
    assert len(body["top_at_risk"]) == 5
    scores = [t["composite_score"] for t in body["top_at_risk"]]
    assert scores == sorted(scores, reverse=True)


def test_create_and_list_interventions(seeded_and_scored, client, db):
    interp_id = str(db.execute(select(Interpreter.id).limit(1)).scalar_one())
    r = client.post(
        "/api/interventions",
        json={
            "interpreter_id": interp_id,
            "action": InterventionAction.coach_call.value,
            "notes": "Discussed evening-only availability",
        },
    )
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["interpreter_id"] == interp_id
    assert created["action"] == "coach_call"

    r2 = client.get(f"/api/interventions?interpreter_id={interp_id}")
    assert r2.status_code == 200
    body = r2.json()
    assert body["total"] >= 1
    assert any(item["id"] == created["id"] for item in body["items"])


def test_create_intervention_unknown_interpreter(seeded_and_scored, client):
    r = client.post(
        "/api/interventions",
        json={
            "interpreter_id": "00000000-0000-0000-0000-000000000000",
            "action": InterventionAction.coach_call.value,
        },
    )
    assert r.status_code == 400


def test_scores_backfill_endpoint(seeded_and_scored, client):
    r = client.post("/api/scores/backfill?days=7&end=2026-08-21")
    assert r.status_code == 200
    body = r.json()
    assert body["end"] == "2026-08-21"
    assert body["days"] == 7
    assert body["total_scored"] == 7 * 200


def test_scores_backfill_days_cap(seeded_and_scored, client):
    r = client.post("/api/scores/backfill?days=500")
    assert r.status_code == 422  # FastAPI validates Query(le=90)
