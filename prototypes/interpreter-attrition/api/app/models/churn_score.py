import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.enums import ChurnBand
from app.models.base import Base


class ChurnScore(Base):
    __tablename__ = "churn_scores"

    interpreter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("interpreters.id", ondelete="CASCADE"),
        primary_key=True,
    )
    as_of: Mapped[date] = mapped_column(Date, primary_key=True)
    composite_score: Mapped[int] = mapped_column(Integer, nullable=False)
    signal_1_volume: Mapped[int] = mapped_column(Integer, nullable=False)
    signal_2_decline: Mapped[int] = mapped_column(Integer, nullable=False)
    signal_3_latency: Mapped[int] = mapped_column(Integer, nullable=False)
    signal_4_feedback: Mapped[int] = mapped_column(Integer, nullable=False)
    signal_5_tenure: Mapped[int] = mapped_column(Integer, nullable=False)
    signal_6_availability: Mapped[int] = mapped_column(Integer, nullable=False)
    band: Mapped[ChurnBand] = mapped_column(
        Enum(ChurnBand, name="churn_band", native_enum=True), nullable=False
    )
