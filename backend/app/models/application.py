import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, LargeBinary, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ApplicationStatus, Base, UUIDPrimaryKeyMixin


class Application(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "applications"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), unique=True
    )
    tailored_resume_pdf: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )
    tailored_content: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status_enum"),
        default=ApplicationStatus.generated,
    )
    applied_at: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    job: Mapped["Job"] = relationship(back_populates="application")
