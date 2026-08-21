import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.enums import InterventionAction
from app.models.base import Base


class Intervention(Base):
    __tablename__ = "interventions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interpreter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interpreters.id", ondelete="CASCADE"),
        nullable=False,
    )
    action: Mapped[InterventionAction] = mapped_column(
        Enum(InterventionAction, name="intervention_action", native_enum=True), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    outcome: Mapped[str | None] = mapped_column(String(32), nullable=True)  # 'retained'|'churned'|'pending'

    __table_args__ = (
        Index("ix_interventions_interpreter_created", "interpreter_id", "created_at"),
    )
