"""Read-side Pydantic schemas returned by the dashboard/interpreter/timeline
/interventions endpoints. All are response models — request-side validation
lives in ingest.py."""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.enums import ChurnBand, InterpreterStatus, InterventionAction


class SignalReadout(BaseModel):
    key: int  # 1-6
    name: str  # e.g. "Session volume decline"
    score: int  # 0-100
    weight: int  # SPEC weight
    why: str  # plain-English explanation


class LatestScore(BaseModel):
    as_of: date
    composite_score: int
    band: ChurnBand
    top_signal_key: int | None = None


class InterpreterListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    external_id: str
    full_name: str
    languages: list[str]
    tenure_days: int
    status: InterpreterStatus
    latest_score: LatestScore | None
    last_session_at: datetime | None


class InterpreterListResponse(BaseModel):
    items: list[InterpreterListItem]
    total: int
    limit: int
    offset: int


class InterpreterDetail(BaseModel):
    id: UUID
    external_id: str
    full_name: str
    languages: list[str]
    certifications: list[str]
    hired_at: date
    tenure_days: int
    status: InterpreterStatus
    home_timezone: str | None
    latest_score: LatestScore | None
    signals: list[SignalReadout]
    last_session_at: datetime | None
    recent_intervention_count: int


class TimelinePoint(BaseModel):
    as_of: date
    composite_score: int
    signal_1_volume: int
    signal_2_decline: int
    signal_3_latency: int
    signal_4_feedback: int
    signal_5_tenure: int
    signal_6_availability: int


class TimelineResponse(BaseModel):
    interpreter_id: UUID
    days: int
    points: list[TimelinePoint]


class TopAtRisk(BaseModel):
    id: UUID
    external_id: str
    full_name: str
    languages: list[str]
    composite_score: int
    band: ChurnBand


class DashboardSummary(BaseModel):
    as_of: date
    total_active: int
    band_counts: dict[str, int]  # {"red": 48, "yellow": 88, "green": 264}
    week_over_week: dict[str, int]  # {"red_delta": +3, "yellow_delta": -2, "green_delta": -1}
    top_at_risk: list[TopAtRisk]


class InterventionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interpreter_id: UUID
    action: InterventionAction
    notes: str | None = None
    outcome: str | None = Field(default=None, max_length=32)


class InterventionRead(BaseModel):
    """POST /api/interventions response — just the row."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    interpreter_id: UUID
    action: InterventionAction
    notes: str | None
    created_at: datetime
    outcome: str | None


class InterventionListItem(BaseModel):
    """GET /api/interventions row — enriched with interpreter identity so
    the interventions screen doesn't need per-row lookups."""

    id: UUID
    interpreter_id: UUID
    interpreter_name: str
    interpreter_external_id: str
    action: InterventionAction
    notes: str | None
    created_at: datetime
    outcome: str | None


class InterventionListResponse(BaseModel):
    items: list[InterventionListItem]
    total: int
    limit: int
    offset: int
