"""Enums used across models, schemas, and Alembic migrations.

Keeping names centralized so the Postgres enum types and the Python
enums never drift. Each Python enum's `value` is the exact string
persisted in Postgres.
"""
import enum


class InterpreterStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    inactive = "inactive"


class SessionType(str, enum.Enum):
    opi = "opi"
    vri = "vri"
    onsite = "onsite"


class SessionOutcome(str, enum.Enum):
    completed = "completed"
    dropped = "dropped"
    no_show = "no_show"
    cancelled = "cancelled"


class DispatchResponse(str, enum.Enum):
    accepted = "accepted"
    declined = "declined"
    timeout = "timeout"


class InterventionAction(str, enum.Enum):
    coach_call = "coach_call"
    assign_mentor = "assign_mentor"
    schedule_flex = "schedule_flex"
    comp_bonus = "comp_bonus"
    no_action = "no_action"


class ChurnBand(str, enum.Enum):
    green = "green"
    yellow = "yellow"
    red = "red"


# Postgres type-name → Python enum. Alembic + SQLAlchemy reference these.
PG_ENUM_TYPES: dict[str, type[enum.Enum]] = {
    "interpreter_status": InterpreterStatus,
    "session_type": SessionType,
    "session_outcome": SessionOutcome,
    "dispatch_response": DispatchResponse,
    "intervention_action": InterventionAction,
    "churn_band": ChurnBand,
}
