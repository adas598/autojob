import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class JobType(str, enum.Enum):
    full_time = "full_time"
    part_time = "part_time"
    contract = "contract"
    intern = "intern"


class Seniority(str, enum.Enum):
    junior = "junior"
    mid = "mid"
    senior = "senior"
    lead = "lead"
    exec = "exec"


class VisaStatus(str, enum.Enum):
    authorized = "authorized"
    will_sponsor = "will_sponsor"
    citizen_only = "citizen_only"
    not_specified = "not_specified"


class Portal(str, enum.Enum):
    linkedin = "linkedin"
    indeed = "indeed"
    glassdoor = "glassdoor"
    wellfound = "wellfound"
    seek = "seek"


class ApplicationStatus(str, enum.Enum):
    generated = "generated"
    applied = "applied"
    interview = "interview"
    rejected = "rejected"
    offer = "offer"


class ScrapeRunStatus(str, enum.Enum):
    running = "running"
    success = "success"
    failed = "failed"


class UsageOperation(str, enum.Enum):
    match = "match"
    resume_gen = "resume_gen"
    parse = "parse"
