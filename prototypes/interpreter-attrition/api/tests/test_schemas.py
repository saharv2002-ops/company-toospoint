"""No-DB unit tests for Pydantic ingest schemas."""
from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.enums import DispatchResponse, SessionOutcome, SessionType
from app.schemas.ingest import (
    MAX_BATCH_SIZE,
    DispatchIngest,
    FeedbackIngest,
    IngestBatch,
    InterpreterIngest,
    SessionIngest,
)


def test_interpreter_ingest_defaults():
    row = InterpreterIngest(external_id="ext-1", full_name="Ana", hired_at=date(2025, 1, 1))
    assert row.languages == []
    assert row.status.value == "active"


def test_interpreter_ingest_rejects_extra_field():
    with pytest.raises(ValidationError):
        InterpreterIngest(external_id="x", full_name="y", hired_at=date.today(), foo="bar")


def test_session_ingest_duration_bounds():
    with pytest.raises(ValidationError):
        SessionIngest(
            id=uuid4(),
            interpreter_external_id="ext-1",
            session_type=SessionType.opi,
            language_pair="en-es",
            started_at=datetime.now(timezone.utc),
            duration_seconds=-1,
            outcome=SessionOutcome.completed,
        )


def test_dispatch_response_coercion():
    d = DispatchIngest(
        id=uuid4(),
        interpreter_external_id="ext-1",
        offered_at=datetime.now(timezone.utc),
        response="accepted",
        language_pair="en-es",
    )
    assert d.response is DispatchResponse.accepted


def test_feedback_rating_range():
    with pytest.raises(ValidationError):
        FeedbackIngest(
            id=uuid4(),
            session_id=uuid4(),
            rating=7,
            submitted_at=datetime.now(timezone.utc),
        )


def test_batch_size_lower_bound():
    with pytest.raises(ValidationError):
        IngestBatch[InterpreterIngest](items=[])


def test_batch_size_upper_bound():
    good = [
        InterpreterIngest(external_id=f"ext-{i}", full_name="x", hired_at=date.today())
        for i in range(MAX_BATCH_SIZE)
    ]
    batch = IngestBatch[InterpreterIngest](items=good)
    assert len(batch.items) == MAX_BATCH_SIZE

    too_many = good + [
        InterpreterIngest(external_id="one-more", full_name="x", hired_at=date.today())
    ]
    with pytest.raises(ValidationError):
        IngestBatch[InterpreterIngest](items=too_many)
