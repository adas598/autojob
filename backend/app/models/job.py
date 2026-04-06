import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SAEnum, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class JobStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    applied = "applied"


class MatchScore(str, enum.Enum):
    strong = "strong"
    possible = "possible"
    weak = "weak"


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("url", name="uq_jobs_url"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(500))
    company: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255), default="")
    salary: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    requirements: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(String(1000))
    source: Mapped[str] = mapped_column(String(100))  # seek | iworkfornsw | apsjobs | company
    date_posted: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[JobStatus] = mapped_column(SAEnum(JobStatus), default=JobStatus.pending)
    match_score: Mapped[MatchScore | None] = mapped_column(SAEnum(MatchScore), nullable=True)
    match_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    application: Mapped["Application | None"] = relationship(  # noqa: F821
        "Application", back_populates="job", uselist=False
    )
    applied_history: Mapped[list["AppliedHistory"]] = relationship(  # noqa: F821
        "AppliedHistory", back_populates="job"
    )
