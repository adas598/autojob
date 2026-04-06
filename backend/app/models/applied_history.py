import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ApplicationStatus(str, enum.Enum):
    applied = "applied"
    interview = "interview"
    offer = "offer"
    rejected = "rejected"


class AppliedHistory(Base):
    __tablename__ = "applied_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"))
    status: Mapped[ApplicationStatus] = mapped_column(SAEnum(ApplicationStatus))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    job: Mapped["Job"] = relationship("Job", back_populates="applied_history")  # noqa: F821
