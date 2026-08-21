import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.enums import DispatchResponse
from app.models.base import Base


class Dispatch(Base):
    __tablename__ = "dispatches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interpreter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interpreters.id", ondelete="CASCADE"),
        nullable=False,
    )
    offered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response: Mapped[DispatchResponse] = mapped_column(
        Enum(DispatchResponse, name="dispatch_response", native_enum=True), nullable=False
    )
    language_pair: Mapped[str] = mapped_column(String(16), nullable=False)

    __table_args__ = (
        Index("ix_dispatches_interpreter_offered", "interpreter_id", "offered_at"),
    )
