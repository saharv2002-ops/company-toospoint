"""initial schema — 7 tables (interpreters, sessions, dispatches, feedback,
availability_snapshots, interventions, churn_scores) + 6 native pg enums.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    interpreter_status = postgresql.ENUM(
        "active", "paused", "inactive", name="interpreter_status", create_type=False
    )
    session_type = postgresql.ENUM("opi", "vri", "onsite", name="session_type", create_type=False)
    session_outcome = postgresql.ENUM(
        "completed", "dropped", "no_show", "cancelled", name="session_outcome", create_type=False
    )
    dispatch_response = postgresql.ENUM(
        "accepted", "declined", "timeout", name="dispatch_response", create_type=False
    )
    intervention_action = postgresql.ENUM(
        "coach_call",
        "assign_mentor",
        "schedule_flex",
        "comp_bonus",
        "no_action",
        name="intervention_action",
        create_type=False,
    )
    churn_band = postgresql.ENUM("green", "yellow", "red", name="churn_band", create_type=False)

    bind = op.get_bind()
    for enum_ddl in (
        interpreter_status,
        session_type,
        session_outcome,
        dispatch_response,
        intervention_action,
        churn_band,
    ):
        enum_ddl.create(bind, checkfirst=True)

    op.create_table(
        "interpreters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_id", sa.String(128), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("languages", postgresql.ARRAY(sa.String(8)), nullable=False, server_default="{}"),
        sa.Column(
            "certifications",
            postgresql.ARRAY(sa.String(64)),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("hired_at", sa.Date, nullable=False),
        sa.Column("status", interpreter_status, nullable=False, server_default="active"),
        sa.Column("home_timezone", sa.String(64), nullable=True),
        sa.UniqueConstraint("external_id", name="uq_interpreters_external_id"),
    )

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "interpreter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interpreters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("session_type", session_type, nullable=False),
        sa.Column("language_pair", sa.String(16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_seconds", sa.Integer, nullable=False, server_default="0"),
        sa.Column("outcome", session_outcome, nullable=False),
    )
    op.create_index("ix_sessions_interpreter_started", "sessions", ["interpreter_id", "started_at"])

    op.create_table(
        "dispatches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "interpreter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interpreters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("offered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response", dispatch_response, nullable=False),
        sa.Column("language_pair", sa.String(16), nullable=False),
    )
    op.create_index(
        "ix_dispatches_interpreter_offered", "dispatches", ["interpreter_id", "offered_at"]
    )

    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rating", sa.Integer, nullable=True),
        sa.Column("complaint_flag", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "rating IS NULL OR (rating BETWEEN 1 AND 5)", name="ck_feedback_rating_range"
        ),
    )
    op.create_index("ix_feedback_session", "feedback", ["session_id"])

    op.create_table(
        "availability_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "interpreter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interpreters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("week_of", sa.Date, nullable=False),
        sa.Column("hours_declared", sa.Numeric(6, 2), nullable=False, server_default="0"),
        sa.UniqueConstraint("interpreter_id", "week_of", name="uq_availability_interpreter_week"),
    )

    op.create_table(
        "interventions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "interpreter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interpreters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", intervention_action, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("outcome", sa.String(32), nullable=True),
    )
    op.create_index(
        "ix_interventions_interpreter_created", "interventions", ["interpreter_id", "created_at"]
    )

    op.create_table(
        "churn_scores",
        sa.Column(
            "interpreter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("interpreters.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("as_of", sa.Date, primary_key=True),
        sa.Column("composite_score", sa.Integer, nullable=False),
        sa.Column("signal_1_volume", sa.Integer, nullable=False),
        sa.Column("signal_2_decline", sa.Integer, nullable=False),
        sa.Column("signal_3_latency", sa.Integer, nullable=False),
        sa.Column("signal_4_feedback", sa.Integer, nullable=False),
        sa.Column("signal_5_tenure", sa.Integer, nullable=False),
        sa.Column("signal_6_availability", sa.Integer, nullable=False),
        sa.Column("band", churn_band, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("churn_scores")
    op.drop_index("ix_interventions_interpreter_created", table_name="interventions")
    op.drop_table("interventions")
    op.drop_table("availability_snapshots")
    op.drop_index("ix_feedback_session", table_name="feedback")
    op.drop_table("feedback")
    op.drop_index("ix_dispatches_interpreter_offered", table_name="dispatches")
    op.drop_table("dispatches")
    op.drop_index("ix_sessions_interpreter_started", table_name="sessions")
    op.drop_table("sessions")
    op.drop_table("interpreters")
    for enum_name in (
        "churn_band",
        "intervention_action",
        "dispatch_response",
        "session_outcome",
        "session_type",
        "interpreter_status",
    ):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
