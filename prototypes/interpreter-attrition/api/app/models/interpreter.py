import uuid
from datetime import date

from sqlalchemy import Date, Enum, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.enums import InterpreterStatus
from app.models.base import Base


class Interpreter(Base):
    __tablename__ = "interpreters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    languages: Mapped[list[str]] = mapped_column(ARRAY(String(8)), nullable=False, default=list)
    certifications: Mapped[list[str]] = mapped_column(ARRAY(String(64)), nullable=False, default=list)
    hired_at: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[InterpreterStatus] = mapped_column(
        Enum(InterpreterStatus, name="interpreter_status", native_enum=True),
        nullable=False,
        default=InterpreterStatus.active,
    )
    home_timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (UniqueConstraint("external_id", name="uq_interpreters_external_id"),)
