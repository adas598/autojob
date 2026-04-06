from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Profile(Base, TimestampMixin):
    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(primary_key=True)  # always 1, single-user tool
    name: Mapped[str] = mapped_column(String(255), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    location: Mapped[str] = mapped_column(String(255), default="")
    visa_type: Mapped[str] = mapped_column(String(50), default="")
    visa_expiry: Mapped[str] = mapped_column(String(20), default="")
    work_rights: Mapped[str] = mapped_column(String(100), default="Full work rights")
    target_titles: Mapped[list] = mapped_column(JSON, default=list)
    skills: Mapped[list] = mapped_column(JSON, default=list)
    work_history: Mapped[list] = mapped_column(JSON, default=list)
    education: Mapped[list] = mapped_column(JSON, default=list)
    salary_min: Mapped[int | None] = mapped_column(nullable=True)
    salary_max: Mapped[int | None] = mapped_column(nullable=True)
    preferred_locations: Mapped[list] = mapped_column(JSON, default=list)
    exclusion_keywords: Mapped[list] = mapped_column(JSON, default=list)
    exclusion_companies: Mapped[list] = mapped_column(JSON, default=list)
    resume_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    writing_sample_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
