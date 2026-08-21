import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.enums import SessionOutcome, SessionType
from app.models.base import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interpreter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interpreters.id", ondelete="CASCADE"),
        nullable=False,
    )
    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    session_type: Mapped[SessionType] = mapped_column(
        Enum(SessionType, name="session_type", native_enum=True), nullable=False
    )
    language_pair: Mapped[str] = mapped_column(String(16), nullable=False)  # 'en-es'
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    outcome: Mapped[SessionOutcome] = mapped_column(
        Enum(SessionOutcome, name="session_outcome", native_enum=True), nullable=False
    )

    __table_args__ = (
        Index("ix_sessions_interpreter_started", "interpreter_id", "started_at"),
    )
