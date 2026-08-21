import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AvailabilitySnapshot(Base):
    __tablename__ = "availability_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interpreter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interpreters.id", ondelete="CASCADE"),
        nullable=False,
    )
    week_of: Mapped[date] = mapped_column(Date, nullable=False)
    hours_declared: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("interpreter_id", "week_of", name="uq_availability_interpreter_week"),
    )
