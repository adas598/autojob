from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, LargeBinary, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Resume(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resumes"

    file_name: Mapped[str] = mapped_column(String(255))
    raw_text: Mapped[str] = mapped_column(Text, default="")
    parsed_skills: Mapped[dict] = mapped_column(JSONB, default=list)
    parsed_experience: Mapped[dict] = mapped_column(JSONB, default=list)
    parsed_education: Mapped[dict] = mapped_column(JSONB, default=list)
    pdf_blob: Mapped[bytes] = mapped_column(LargeBinary)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    scores: Mapped[list["JobScore"]] = relationship(back_populates="resume")
