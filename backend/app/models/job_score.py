import uuid

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class JobScore(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "job_scores"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE")
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="CASCADE")
    )
    overall_score: Mapped[int] = mapped_column(Integer)
    rubric_breakdown: Mapped[dict] = mapped_column(JSONB, default=dict)
    reasoning: Mapped[str] = mapped_column(Text, default="")
    scored_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True))

    job: Mapped["Job"] = relationship(back_populates="scores")
    resume: Mapped["Resume"] = relationship(back_populates="scores")
