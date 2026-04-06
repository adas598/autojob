from sqlalchemy import Enum, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    JobType,
    Portal,
    Seniority,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    VisaStatus,
)


class Job(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("portal", "external_id", name="uq_job_portal_external_id"),
    )

    title: Mapped[str] = mapped_column(String(500))
    company: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255), default="")
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    job_type: Mapped[JobType | None] = mapped_column(
        Enum(JobType, name="job_type_enum"), nullable=True
    )
    seniority: Mapped[Seniority | None] = mapped_column(
        Enum(Seniority, name="seniority_enum"), nullable=True
    )
    visa_status: Mapped[list[VisaStatus]] = mapped_column(
        ARRAY(Enum(VisaStatus, name="visa_status_enum", create_constraint=False)),
        default=list,
    )
    description: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str] = mapped_column(String(2048), default="")
    portal: Mapped[Portal] = mapped_column(Enum(Portal, name="portal_enum"))
    external_id: Mapped[str] = mapped_column(String(255))
    scraped_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True))

    scores: Mapped[list["JobScore"]] = relationship(back_populates="job")
    application: Mapped["Application | None"] = relationship(back_populates="job")
