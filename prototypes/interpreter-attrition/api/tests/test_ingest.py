"""Integration tests for POST /api/ingest/* against real Postgres.

Skipped when POSTGRES_TEST_URL is not set. See conftest.py.
"""
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.models import (
    AvailabilitySnapshot,
    Dispatch,
    Feedback,
    Interpreter,
    Intervention,
)
from app.models import Session as SessionModel
from tests.conftest import requires_postgres

pytestmark = requires_postgres

NOW = datetime.now(timezone.utc)


def _post(client, path, items):
    r = client.post(path, json={"items": items})
    return r


def _seed_interpreters(client, count):
    items = [
        {
            "external_id": f"ext-{i}",
            "full_name": f"Interp {i}",
            "languages": ["en", "es"],
            "certifications": [],
            "hired_at": (date.today() - timedelta(days=200 + i)).isoformat(),
            "status": "active",
        }
        for i in range(count)
    ]
    r = _post(client, "/api/ingest/interpreters", items)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == count


def test_interpreters_insert_and_reinsert_idempotent(client, db):
    _seed_interpreters(client, 100)
    assert db.execute(select(func.count(Interpreter.id))).scalar_one() == 100

    _seed_interpreters(client, 100)  # same payload
    assert db.execute(select(func.count(Interpreter.id))).scalar_one() == 100

    row = db.execute(select(Interpreter).where(Interpreter.external_id == "ext-0")).scalar_one()
    assert row.full_name == "Interp 0"
    assert row.languages == ["en", "es"]


def test_sessions_ingest_and_reingest(client, db):
    _seed_interpreters(client, 5)
    items = [
        {
            "id": str(uuid4()),
            "interpreter_external_id": f"ext-{i % 5}",
            "session_type": "opi",
            "language_pair": "en-es",
            "started_at": (NOW - timedelta(hours=i)).isoformat(),
            "duration_seconds": 600 + i,
            "outcome": "completed",
        }
        for i in range(100)
    ]
    assert _post(client, "/api/ingest/sessions", items).status_code == 200
    assert db.execute(select(func.count(SessionModel.id))).scalar_one() == 100

    # Re-post with a change on the first item
    items[0]["duration_seconds"] = 9999
    assert _post(client, "/api/ingest/sessions", items).status_code == 200
    assert db.execute(select(func.count(SessionModel.id))).scalar_one() == 100
    row = db.execute(
        select(SessionModel).where(SessionModel.id == items[0]["id"])
    ).scalar_one()
    assert row.duration_seconds == 9999


def test_sessions_unknown_interpreter_rejected(client):
    _seed_interpreters(client, 1)
    items = [
        {
            "id": str(uuid4()),
            "interpreter_external_id": "does-not-exist",
            "session_type": "vri",
            "language_pair": "en-fr",
            "started_at": NOW.isoformat(),
            "duration_seconds": 300,
            "outcome": "completed",
        }
    ]
    r = _post(client, "/api/ingest/sessions", items)
    assert r.status_code == 400
    assert r.json()["detail"]["error"] == "unknown_interpreter_external_ids"


def test_dispatches_ingest(client, db):
    _seed_interpreters(client, 5)
    items = [
        {
            "id": str(uuid4()),
            "interpreter_external_id": f"ext-{i % 5}",
            "offered_at": (NOW - timedelta(minutes=i)).isoformat(),
            "responded_at": (NOW - timedelta(minutes=i, seconds=-5)).isoformat(),
            "response": "accepted" if i % 3 else "declined",
            "language_pair": "en-es",
        }
        for i in range(100)
    ]
    assert _post(client, "/api/ingest/dispatches", items).status_code == 200
    assert db.execute(select(func.count(Dispatch.id))).scalar_one() == 100

    assert _post(client, "/api/ingest/dispatches", items).status_code == 200
    assert db.execute(select(func.count(Dispatch.id))).scalar_one() == 100


def test_feedback_ingest(client, db):
    _seed_interpreters(client, 2)
    session_items = [
        {
            "id": str(uuid4()),
            "interpreter_external_id": "ext-0",
            "session_type": "opi",
            "language_pair": "en-es",
            "started_at": NOW.isoformat(),
            "duration_seconds": 500,
            "outcome": "completed",
        }
        for _ in range(3)
    ]
    _post(client, "/api/ingest/sessions", session_items)

    feedback_items = [
        {
            "id": str(uuid4()),
            "session_id": s["id"],
            "rating": 5,
            "complaint_flag": False,
            "submitted_at": NOW.isoformat(),
        }
        for s in session_items
    ]
    assert _post(client, "/api/ingest/feedback", feedback_items).status_code == 200
    assert db.execute(select(func.count(Feedback.id))).scalar_one() == 3

    # re-post with an updated rating on the first
    feedback_items[0]["rating"] = 2
    feedback_items[0]["complaint_flag"] = True
    assert _post(client, "/api/ingest/feedback", feedback_items).status_code == 200
    assert db.execute(select(func.count(Feedback.id))).scalar_one() == 3
    row = db.execute(
        select(Feedback).where(Feedback.id == feedback_items[0]["id"])
    ).scalar_one()
    assert row.rating == 2
    assert row.complaint_flag is True


def test_availability_ingest_unique_by_week(client, db):
    _seed_interpreters(client, 3)
    items = [
        {
            "interpreter_external_id": f"ext-{i % 3}",
            "week_of": (date.today() - timedelta(weeks=w)).isoformat(),
            "hours_declared": "20.0",
        }
        for i in range(3)
        for w in range(4)
    ]
    assert _post(client, "/api/ingest/availability", items).status_code == 200
    assert db.execute(select(func.count(AvailabilitySnapshot.id))).scalar_one() == 12

    # re-post updates hours in place
    for item in items:
        item["hours_declared"] = "30.0"
    assert _post(client, "/api/ingest/availability", items).status_code == 200
    assert db.execute(select(func.count(AvailabilitySnapshot.id))).scalar_one() == 12
    row = db.execute(select(AvailabilitySnapshot).limit(1)).scalar_one()
    assert float(row.hours_declared) == 30.0


def test_interventions_ingest_insert_only(client, db):
    _seed_interpreters(client, 2)
    items = [
        {"interpreter_external_id": "ext-0", "action": "coach_call", "notes": "morning check-in"},
        {"interpreter_external_id": "ext-1", "action": "schedule_flex"},
    ]
    assert _post(client, "/api/ingest/interventions", items).status_code == 200
    assert db.execute(select(func.count(Intervention.id))).scalar_one() == 2

    assert _post(client, "/api/ingest/interventions", items).status_code == 200
    assert db.execute(select(func.count(Intervention.id))).scalar_one() == 4


def test_empty_batch_rejected(client):
    r = client.post("/api/ingest/interpreters", json={"items": []})
    assert r.status_code == 422


def test_oversized_payload_rejected(client):
    # Craft a Content-Length header claiming 20MB
    r = client.post(
        "/api/ingest/interpreters",
        content=b'{"items":[]}',
        headers={"content-length": str(20 * 1024 * 1024), "content-type": "application/json"},
    )
    assert r.status_code == 413
