"""Pydantic 2 schemas for the /api/ingest/* endpoints.

Each entity has an *Ingest schema. Requests come in as `IngestBatch[T]`
so validators and payload guards live in one place.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.enums import (
    DispatchResponse,
    InterpreterStatus,
    InterventionAction,
    SessionOutcome,
    SessionType,
)

# Cap batch size at 5,000 rows per request — protects the API from
# accidental multi-million-row uploads and keeps payloads under the
# 10MB middleware limit for reasonable rows.
MAX_BATCH_SIZE = 5_000

LangCode = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=8)]
LangPair = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=16)]
ExternalId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)]


class InterpreterIngest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_id: ExternalId
    full_name: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    languages: list[LangCode] = Field(default_factory=list)
    certifications: list[Annotated[str, StringConstraints(max_length=64)]] = Field(default_factory=list)
    hired_at: date
    status: InterpreterStatus = InterpreterStatus.active
    home_timezone: Annotated[str, StringConstraints(max_length=64)] | None = None


class SessionIngest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    interpreter_external_id: ExternalId
    client_id: UUID | None = None
    session_type: SessionType
    language_pair: LangPair
    started_at: datetime
    duration_seconds: int = Field(ge=0, le=24 * 60 * 60)
    outcome: SessionOutcome


class DispatchIngest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    interpreter_external_id: ExternalId
    offered_at: datetime
    responded_at: datetime | None = None
    response: DispatchResponse
    language_pair: LangPair


class FeedbackIngest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    session_id: UUID
    rating: int | None = Field(default=None, ge=1, le=5)
    complaint_flag: bool = False
    category: Annotated[str, StringConstraints(max_length=64)] | None = None
    notes: str | None = None
    submitted_at: datetime


class AvailabilitySnapshotIngest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interpreter_external_id: ExternalId
    week_of: date
    hours_declared: Decimal = Field(ge=0, le=168)


class InterventionIngest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interpreter_external_id: ExternalId
    action: InterventionAction
    notes: str | None = None
    outcome: Annotated[str, StringConstraints(max_length=32)] | None = None


T = TypeVar("T", bound=BaseModel)


class IngestBatch(BaseModel, Generic[T]):
    """Envelope for a batch of rows to ingest."""

    model_config = ConfigDict(extra="forbid")

    items: list[T] = Field(min_length=1, max_length=MAX_BATCH_SIZE)


class IngestResult(BaseModel):
    inserted: int
    updated: int
    total: int
