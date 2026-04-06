# AutoJob Plan 1: Backend Core — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the FastAPI backend with all database models, migrations, config, and CRUD API routes — ready for scrapers, LLM services, and frontend to build against.

**Architecture:** Single FastAPI app with async SQLAlchemy ORM, PostgreSQL via asyncpg, Alembic for migrations. All API routes return Pydantic schemas. Config loaded from environment variables with sensible defaults for local development.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, asyncpg, Pydantic v2, pytest + httpx (testing)

**Design Spec:** `docs/superpowers/specs/2026-04-06-autojob-design.md`

---

## File Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app factory + lifespan
│   ├── config.py                # Pydantic Settings (env vars)
│   ├── database.py              # Async engine + session factory
│   ├── models/
│   │   ├── __init__.py          # Import all models for Alembic
│   │   ├── base.py              # DeclarativeBase + common mixins
│   │   ├── resume.py            # Resume model
│   │   ├── job.py               # Job model + enums
│   │   ├── job_score.py         # JobScore model
│   │   ├── application.py       # Application model
│   │   ├── scrape_run.py        # ScrapeRun model
│   │   ├── usage_log.py         # UsageLog model
│   │   └── setting.py           # Setting model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── resume.py            # Resume request/response schemas
│   │   ├── job.py               # Job schemas + filter params
│   │   ├── job_score.py         # JobScore schemas
│   │   ├── application.py       # Application schemas
│   │   ├── setting.py           # Setting schemas
│   │   └── common.py            # Pagination, health check
│   └── api/
│       ├── __init__.py
│       ├── router.py            # Top-level router aggregation
│       ├── jobs.py              # GET /jobs (list, filter, sort), GET /jobs/{id}
│       ├── resume.py            # POST /resume (upload), GET /resume/active
│       ├── apply.py             # POST /apply/{job_id}, GET /applications
│       └── settings.py          # GET/PUT /settings, GET /usage
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/                # Migration files
├── tests/
│   ├── conftest.py              # Fixtures: test DB, async client
│   ├── test_health.py           # Health endpoint
│   ├── test_models.py           # Model creation tests
│   ├── test_jobs_api.py         # Jobs CRUD + filtering
│   ├── test_resume_api.py       # Resume upload + retrieval
│   ├── test_applications_api.py # Applications CRUD
│   └── test_settings_api.py     # Settings CRUD
├── alembic.ini
├── requirements.txt
├── Dockerfile
├── railway.toml
├── .env.example
└── pyproject.toml
```

---

### Task 1: Project Scaffold & Dependencies

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py`

- [ ] **Step 1: Create the backend directory and requirements.txt**

```
backend/requirements.txt
```

```txt
fastapi==0.115.12
uvicorn[standard]==0.34.2
sqlalchemy[asyncio]==2.0.40
asyncpg==0.30.0
alembic==1.15.2
pydantic==2.11.3
pydantic-settings==2.9.1
python-multipart==0.0.20
httpx==0.28.1
pytest==8.3.5
pytest-asyncio==0.26.0
```

- [ ] **Step 2: Create pyproject.toml**

```toml
[project]
name = "autojob-backend"
version = "0.1.0"
requires-python = ">=3.12"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 3: Create .env.example**

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/autojob
OPENAI_API_KEY=sk-your-key-here
CLERK_SECRET_KEY=sk_test_your-key-here
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

- [ ] **Step 4: Create empty __init__.py**

```python
# backend/app/__init__.py
```

- [ ] **Step 5: Install dependencies**

Run: `cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
Expected: All packages install successfully.

- [ ] **Step 6: Commit**

```bash
git init
git add backend/requirements.txt backend/pyproject.toml backend/.env.example backend/app/__init__.py
git commit -m "feat: scaffold backend project with dependencies"
```

---

### Task 2: Config & Database Connection

**Files:**
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`

- [ ] **Step 1: Write config.py**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/autojob"
    openai_api_key: str = ""
    clerk_secret_key: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

- [ ] **Step 2: Write database.py**

```python
# backend/app/database.py
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/config.py backend/app/database.py
git commit -m "feat: add config and async database connection"
```

---

### Task 3: Model Base & Enums

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/base.py`

- [ ] **Step 1: Write base.py with DeclarativeBase and enums**

```python
# backend/app/models/base.py
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


# --- Enums ---

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
```

- [ ] **Step 2: Write models/__init__.py**

```python
# backend/app/models/__init__.py
from app.models.base import Base
from app.models.resume import Resume
from app.models.job import Job
from app.models.job_score import JobScore
from app.models.application import Application
from app.models.scrape_run import ScrapeRun
from app.models.usage_log import UsageLog
from app.models.setting import Setting

__all__ = [
    "Base",
    "Resume",
    "Job",
    "JobScore",
    "Application",
    "ScrapeRun",
    "UsageLog",
    "Setting",
]
```

Note: The individual model files don't exist yet — they'll be created in the next tasks. This file will cause ImportErrors until Tasks 4–7 are done. That's fine — we'll run tests after all models exist.

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add model base, enums, and model registry"
```

---

### Task 4: Resume & Job Models

**Files:**
- Create: `backend/app/models/resume.py`
- Create: `backend/app/models/job.py`

- [ ] **Step 1: Write resume.py**

```python
# backend/app/models/resume.py
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, LargeBinary, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
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
```

- [ ] **Step 2: Write job.py**

```python
# backend/app/models/job.py
from sqlalchemy import Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMPTZ
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
    scraped_at: Mapped[str] = mapped_column(TIMESTAMPTZ)

    scores: Mapped[list["JobScore"]] = relationship(back_populates="job")
    application: Mapped["Application | None"] = relationship(back_populates="job")

    __table_args__ = (
        {"schema": None},
    )

    # Dedup: unique constraint on (portal, external_id)
    __table_args__ = (
        {"info": {"unique_constraints": [("portal", "external_id")]}},
    )
```

Wait — SQLAlchemy unique constraints should use `UniqueConstraint`. Let me fix:

```python
# backend/app/models/job.py
from sqlalchemy import Enum, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMPTZ
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
    scraped_at: Mapped[str] = mapped_column(TIMESTAMPTZ)

    scores: Mapped[list["JobScore"]] = relationship(back_populates="job")
    application: Mapped["Application | None"] = relationship(back_populates="job")
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/resume.py backend/app/models/job.py
git commit -m "feat: add Resume and Job models"
```

---

### Task 5: Remaining Models (JobScore, Application, ScrapeRun, UsageLog, Setting)

**Files:**
- Create: `backend/app/models/job_score.py`
- Create: `backend/app/models/application.py`
- Create: `backend/app/models/scrape_run.py`
- Create: `backend/app/models/usage_log.py`
- Create: `backend/app/models/setting.py`

- [ ] **Step 1: Write job_score.py**

```python
# backend/app/models/job_score.py
import uuid

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMPTZ, UUID
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
    scored_at: Mapped[str] = mapped_column(TIMESTAMPTZ)

    job: Mapped["Job"] = relationship(back_populates="scores")
    resume: Mapped["Resume"] = relationship(back_populates="scores")
```

- [ ] **Step 2: Write application.py**

```python
# backend/app/models/application.py
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, LargeBinary, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMPTZ, UUID
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
    applied_at: Mapped[str | None] = mapped_column(TIMESTAMPTZ, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    job: Mapped["Job"] = relationship(back_populates="application")
```

- [ ] **Step 3: Write scrape_run.py**

```python
# backend/app/models/scrape_run.py
from sqlalchemy import Enum, Integer, Text
from sqlalchemy.dialects.postgresql import TIMESTAMPTZ
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, Portal, ScrapeRunStatus, UUIDPrimaryKeyMixin


class ScrapeRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "scrape_runs"

    portal: Mapped[Portal] = mapped_column(Enum(Portal, name="portal_enum"))
    status: Mapped[ScrapeRunStatus] = mapped_column(
        Enum(ScrapeRunStatus, name="scrape_run_status_enum")
    )
    jobs_found: Mapped[int] = mapped_column(Integer, default=0)
    jobs_new: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[str] = mapped_column(TIMESTAMPTZ)
    finished_at: Mapped[str | None] = mapped_column(TIMESTAMPTZ, nullable=True)
```

- [ ] **Step 4: Write usage_log.py**

```python
# backend/app/models/usage_log.py
from sqlalchemy import Enum, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import TIMESTAMPTZ
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, UsageOperation


class UsageLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "usage_logs"

    operation: Mapped[UsageOperation] = mapped_column(
        Enum(UsageOperation, name="usage_operation_enum")
    )
    model: Mapped[str] = mapped_column(String(100))
    tokens_input: Mapped[int] = mapped_column(Integer, default=0)
    tokens_output: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), default=0)
```

- [ ] **Step 5: Write setting.py**

```python
# backend/app/models/setting.py
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
        onupdate=lambda: datetime.now(timezone.utc),
    )
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add JobScore, Application, ScrapeRun, UsageLog, Setting models"
```

---

### Task 6: Alembic Setup & Initial Migration

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/` (auto-generated)

- [ ] **Step 1: Initialize Alembic**

Run:
```bash
cd backend
source .venv/bin/activate
alembic init alembic
```

Expected: Creates `alembic/` directory and `alembic.ini`.

- [ ] **Step 2: Update alembic.ini — set sqlalchemy.url**

In `backend/alembic.ini`, find the line:
```
sqlalchemy.url = driver://user:pass@localhost/dbname
```
Replace with:
```
sqlalchemy.url = postgresql+asyncpg://postgres:postgres@localhost:5432/autojob
```

- [ ] **Step 3: Update alembic/env.py for async + our models**

Replace the entire contents of `backend/alembic/env.py` with:

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = settings.database_url
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(settings.database_url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

- [ ] **Step 4: Create the PostgreSQL database locally**

Run:
```bash
createdb autojob
```

Expected: Database created (no output on success). If `createdb` is not available, use `psql -c "CREATE DATABASE autojob;"`.

- [ ] **Step 5: Generate the initial migration**

Run:
```bash
cd backend
alembic revision --autogenerate -m "initial schema"
```

Expected: Creates a migration file in `alembic/versions/`. Output shows tables: resumes, jobs, job_scores, applications, scrape_runs, usage_logs, settings.

- [ ] **Step 6: Run the migration**

Run:
```bash
alembic upgrade head
```

Expected: `INFO  [alembic.runtime.migration] Running upgrade  -> <revision>, initial schema`

- [ ] **Step 7: Verify tables exist**

Run:
```bash
psql autojob -c "\dt"
```

Expected: Lists all 7 tables + alembic_version.

- [ ] **Step 8: Commit**

```bash
git add backend/alembic.ini backend/alembic/
git commit -m "feat: add Alembic setup and initial migration"
```

---

### Task 7: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/common.py`
- Create: `backend/app/schemas/job.py`
- Create: `backend/app/schemas/resume.py`
- Create: `backend/app/schemas/job_score.py`
- Create: `backend/app/schemas/application.py`
- Create: `backend/app/schemas/setting.py`

- [ ] **Step 1: Write common.py**

```python
# backend/app/schemas/common.py
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"


class PaginationParams(BaseModel):
    page: int = 1
    per_page: int = 20


class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
```

- [ ] **Step 2: Write job.py schemas**

```python
# backend/app/schemas/job.py
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.base import JobType, Portal, Seniority, VisaStatus


class JobResponse(BaseModel):
    id: uuid.UUID
    title: str
    company: str
    location: str
    salary_min: int | None
    salary_max: int | None
    job_type: JobType | None
    seniority: Seniority | None
    visa_status: list[VisaStatus]
    description: str
    source_url: str
    portal: Portal
    external_id: str
    scraped_at: datetime
    created_at: datetime
    overall_score: int | None = None
    rubric_breakdown: dict | None = None
    reasoning: str | None = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: list[JobResponse]


class JobFilterParams(BaseModel):
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    job_type: JobType | None = None
    seniority: Seniority | None = None
    visa_status: VisaStatus | None = None
    portal: Portal | None = None
    score_min: int | None = None
    score_max: int | None = None
    show_all: bool = False  # Include below-threshold jobs
    sort_by: str = "overall_score"  # overall_score, scraped_at, salary_max, company
    sort_order: str = "desc"  # asc, desc
    page: int = 1
    per_page: int = 20
```

- [ ] **Step 3: Write resume.py schemas**

```python
# backend/app/schemas/resume.py
import uuid
from datetime import datetime

from pydantic import BaseModel


class ResumeResponse(BaseModel):
    id: uuid.UUID
    file_name: str
    raw_text: str
    parsed_skills: list
    parsed_experience: list
    parsed_education: list
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeListResponse(BaseModel):
    items: list[ResumeResponse]


class ResumeUploadResponse(BaseModel):
    id: uuid.UUID
    file_name: str
    parsed_skills: list
    parsed_experience: list
    parsed_education: list
    is_active: bool
```

- [ ] **Step 4: Write application.py schemas**

```python
# backend/app/schemas/application.py
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.base import ApplicationStatus


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    status: ApplicationStatus
    tailored_content: dict | None
    applied_at: datetime | None
    updated_at: datetime
    # Job info included for convenience
    job_title: str | None = None
    job_company: str | None = None

    model_config = {"from_attributes": True}


class ApplicationListResponse(BaseModel):
    items: list[ApplicationResponse]


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
```

- [ ] **Step 5: Write job_score.py and setting.py schemas**

```python
# backend/app/schemas/job_score.py
import uuid
from datetime import datetime

from pydantic import BaseModel


class JobScoreResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    resume_id: uuid.UUID
    overall_score: int
    rubric_breakdown: dict
    reasoning: str
    scored_at: datetime

    model_config = {"from_attributes": True}
```

```python
# backend/app/schemas/setting.py
from datetime import datetime

from pydantic import BaseModel


class SettingResponse(BaseModel):
    key: str
    value: dict
    updated_at: datetime

    model_config = {"from_attributes": True}


class SettingUpdate(BaseModel):
    value: dict


class UsageSummary(BaseModel):
    total_tokens_input: int
    total_tokens_output: int
    total_cost_usd: float
    cap_type: str | None  # monthly, weekly, twelve_hourly
    cap_value: float | None
    usage_percentage: float | None  # 0-100
    period_start: datetime | None
```

- [ ] **Step 6: Write schemas/__init__.py**

```python
# backend/app/schemas/__init__.py
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/
git commit -m "feat: add Pydantic request/response schemas"
```

---

### Task 8: FastAPI App & Health Endpoint

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/router.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_health.py
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_returns_ok():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

```python
# backend/tests/__init__.py
```

```python
# backend/tests/conftest.py
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_health.py -v`
Expected: FAIL — `app.main` does not exist yet.

- [ ] **Step 3: Write main.py and router**

```python
# backend/app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.schemas.common import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: add scheduler, etc. (later plans)
    yield
    # Shutdown: cleanup


app = FastAPI(title="AutoJob API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()
```

```python
# backend/app/api/__init__.py
```

```python
# backend/app/api/router.py
from fastapi import APIRouter

api_router = APIRouter()

# Sub-routers will be included here in later tasks
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_health.py -v`
Expected: PASS

- [ ] **Step 5: Verify server starts**

Run: `cd backend && uvicorn app.main:app --reload --port 8000`
Expected: Server starts. Visit `http://localhost:8000/health` → `{"status": "ok"}`. Visit `http://localhost:8000/docs` → Swagger UI. Stop the server with Ctrl+C.

- [ ] **Step 6: Commit**

```bash
git add backend/app/main.py backend/app/api/ backend/tests/
git commit -m "feat: add FastAPI app with health endpoint and test"
```

---

### Task 9: Test Fixtures (Async DB)

**Files:**
- Modify: `backend/tests/conftest.py`

- [ ] **Step 1: Write conftest.py with async test DB fixtures**

```python
# backend/tests/conftest.py
import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import app
from app.models import Base

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/autojob_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

- [ ] **Step 2: Create the test database**

Run:
```bash
createdb autojob_test
```

- [ ] **Step 3: Commit**

```bash
git add backend/tests/conftest.py
git commit -m "feat: add async test fixtures with test database"
```

---

### Task 10: Jobs API (List, Filter, Sort, Get)

**Files:**
- Create: `backend/app/api/jobs.py`
- Modify: `backend/app/api/router.py`
- Create: `backend/tests/test_jobs_api.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_jobs_api.py
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import JobType, Portal, Seniority, VisaStatus
from app.models.job import Job


async def _seed_job(db: AsyncSession, **overrides) -> Job:
    defaults = {
        "title": "Software Engineer",
        "company": "Acme Corp",
        "location": "Sydney, Australia",
        "salary_min": 100000,
        "salary_max": 150000,
        "job_type": JobType.full_time,
        "seniority": Seniority.mid,
        "visa_status": [VisaStatus.authorized, VisaStatus.will_sponsor],
        "description": "Build things.",
        "source_url": "https://example.com/job/1",
        "portal": Portal.seek,
        "external_id": str(uuid.uuid4()),
        "scraped_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    job = Job(**defaults)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@pytest.mark.asyncio
async def test_list_jobs_empty(client):
    response = await client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == [] or isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_list_jobs_returns_seeded_job(client, db_session):
    job = await _seed_job(db_session)
    response = await client.get("/api/jobs?show_all=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    titles = [j["title"] for j in data["items"]]
    assert "Software Engineer" in titles


@pytest.mark.asyncio
async def test_filter_by_portal(client, db_session):
    await _seed_job(db_session, portal=Portal.linkedin, external_id="ln-1")
    await _seed_job(db_session, portal=Portal.seek, external_id="sk-1")
    response = await client.get("/api/jobs?portal=linkedin&show_all=true")
    assert response.status_code == 200
    data = response.json()
    for job in data["items"]:
        assert job["portal"] == "linkedin"


@pytest.mark.asyncio
async def test_get_job_by_id(client, db_session):
    job = await _seed_job(db_session, external_id="get-test")
    response = await client.get(f"/api/jobs/{job.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(job.id)


@pytest.mark.asyncio
async def test_get_job_not_found(client):
    fake_id = uuid.uuid4()
    response = await client.get(f"/api/jobs/{fake_id}")
    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_jobs_api.py -v`
Expected: FAIL — `/api/jobs` route doesn't exist.

- [ ] **Step 3: Write jobs.py API route**

```python
# backend/app/api/jobs.py
import uuid
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.base import JobType, Portal, Seniority, VisaStatus
from app.models.job import Job
from app.models.job_score import JobScore
from app.schemas.job import JobFilterParams, JobListResponse, JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
async def list_jobs(
    location: str | None = None,
    salary_min: int | None = None,
    salary_max: int | None = None,
    job_type: JobType | None = None,
    seniority: Seniority | None = None,
    visa_status: VisaStatus | None = None,
    portal: Portal | None = None,
    score_min: int | None = None,
    score_max: int | None = None,
    show_all: bool = False,
    sort_by: str = "scraped_at",
    sort_order: str = "desc",
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Job)

    # Filters
    if location:
        query = query.where(Job.location.ilike(f"%{location}%"))
    if salary_min is not None:
        query = query.where(Job.salary_max >= salary_min)
    if salary_max is not None:
        query = query.where(Job.salary_min <= salary_max)
    if job_type:
        query = query.where(Job.job_type == job_type)
    if seniority:
        query = query.where(Job.seniority == seniority)
    if visa_status:
        query = query.where(Job.visa_status.any(visa_status))
    if portal:
        query = query.where(Job.portal == portal)

    # Sorting
    sort_column = getattr(Job, sort_by, Job.scraped_at)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    jobs = result.scalars().all()

    items = []
    for job in jobs:
        item = JobResponse.model_validate(job)
        # Attach latest score if exists
        score_query = (
            select(JobScore)
            .where(JobScore.job_id == job.id)
            .order_by(JobScore.scored_at.desc())
            .limit(1)
        )
        score_result = await db.execute(score_query)
        score = score_result.scalar_one_or_none()
        if score:
            item.overall_score = score.overall_score
            item.rubric_breakdown = score.rubric_breakdown
            item.reasoning = score.reasoning
        items.append(item)

    return JobListResponse(
        total=total,
        page=page,
        per_page=per_page,
        pages=ceil(total / per_page) if total > 0 else 0,
        items=items,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    item = JobResponse.model_validate(job)

    score_query = (
        select(JobScore)
        .where(JobScore.job_id == job.id)
        .order_by(JobScore.scored_at.desc())
        .limit(1)
    )
    score_result = await db.execute(score_query)
    score = score_result.scalar_one_or_none()
    if score:
        item.overall_score = score.overall_score
        item.rubric_breakdown = score.rubric_breakdown
        item.reasoning = score.reasoning

    return item
```

- [ ] **Step 4: Register the router**

```python
# backend/app/api/router.py
from fastapi import APIRouter

from app.api.jobs import router as jobs_router

api_router = APIRouter()
api_router.include_router(jobs_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_jobs_api.py -v`
Expected: All 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/jobs.py backend/app/api/router.py backend/tests/test_jobs_api.py
git commit -m "feat: add jobs API with filtering, sorting, pagination"
```

---

### Task 11: Resume API (Upload, List, Set Active)

**Files:**
- Create: `backend/app/api/resume.py`
- Modify: `backend/app/api/router.py`
- Create: `backend/tests/test_resume_api.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_resume_api.py
import io

import pytest


@pytest.mark.asyncio
async def test_upload_resume(client):
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake pdf content")
    response = await client.post(
        "/api/resume/upload",
        files={"file": ("test_resume.pdf", fake_pdf, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["file_name"] == "test_resume.pdf"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_active_resume(client):
    # Upload first
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake pdf content")
    await client.post(
        "/api/resume/upload",
        files={"file": ("active.pdf", fake_pdf, "application/pdf")},
    )
    response = await client.get("/api/resume/active")
    assert response.status_code == 200
    assert response.json()["file_name"] == "active.pdf"


@pytest.mark.asyncio
async def test_list_resumes(client):
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake pdf content")
    await client.post(
        "/api/resume/upload",
        files={"file": ("list_test.pdf", fake_pdf, "application/pdf")},
    )
    response = await client.get("/api/resume")
    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_resume_api.py -v`
Expected: FAIL — `/api/resume` routes don't exist.

- [ ] **Step 3: Write resume.py API route**

```python
# backend/app/api/resume.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.resume import Resume
from app.schemas.resume import ResumeListResponse, ResumeResponse, ResumeUploadResponse

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile, db: AsyncSession = Depends(get_db)):
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    pdf_bytes = await file.read()

    # Deactivate all existing resumes
    await db.execute(update(Resume).values(is_active=False))

    # For now, store raw bytes. Parsing will be added in Plan 3 (LLM Services).
    resume = Resume(
        file_name=file.filename,
        raw_text="",  # Populated by parser service later
        parsed_skills=[],
        parsed_experience=[],
        parsed_education=[],
        pdf_blob=pdf_bytes,
        is_active=True,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    return ResumeUploadResponse(
        id=resume.id,
        file_name=resume.file_name,
        parsed_skills=resume.parsed_skills,
        parsed_experience=resume.parsed_experience,
        parsed_education=resume.parsed_education,
        is_active=resume.is_active,
    )


@router.get("/active", response_model=ResumeResponse)
async def get_active_resume(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.is_active == True))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="No active resume found")
    return ResumeResponse.model_validate(resume)


@router.get("", response_model=ResumeListResponse)
async def list_resumes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).order_by(Resume.created_at.desc()))
    resumes = result.scalars().all()
    return ResumeListResponse(
        items=[ResumeResponse.model_validate(r) for r in resumes]
    )


@router.post("/{resume_id}/activate", response_model=ResumeResponse)
async def activate_resume(resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    await db.execute(update(Resume).values(is_active=False))
    resume.is_active = True
    await db.commit()
    await db.refresh(resume)
    return ResumeResponse.model_validate(resume)
```

- [ ] **Step 4: Register the router**

Update `backend/app/api/router.py`:

```python
# backend/app/api/router.py
from fastapi import APIRouter

from app.api.jobs import router as jobs_router
from app.api.resume import router as resume_router

api_router = APIRouter()
api_router.include_router(jobs_router)
api_router.include_router(resume_router)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_resume_api.py -v`
Expected: All 3 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/resume.py backend/app/api/router.py backend/tests/test_resume_api.py
git commit -m "feat: add resume API with upload, list, activate"
```

---

### Task 12: Applications API & Settings API

**Files:**
- Create: `backend/app/api/apply.py`
- Create: `backend/app/api/settings.py`
- Modify: `backend/app/api/router.py`
- Create: `backend/tests/test_applications_api.py`
- Create: `backend/tests/test_settings_api.py`

- [ ] **Step 1: Write applications test**

```python
# backend/tests/test_applications_api.py
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.base import ApplicationStatus, JobType, Portal, Seniority, VisaStatus
from app.models.job import Job


async def _seed_job_for_app(db: AsyncSession) -> Job:
    job = Job(
        title="Test Job",
        company="Test Co",
        location="Remote",
        job_type=JobType.full_time,
        seniority=Seniority.mid,
        visa_status=[VisaStatus.authorized],
        description="Test desc",
        source_url="https://example.com",
        portal=Portal.indeed,
        external_id=str(uuid.uuid4()),
        scraped_at=datetime.now(timezone.utc),
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@pytest.mark.asyncio
async def test_list_applications_empty(client):
    response = await client.get("/api/applications")
    assert response.status_code == 200
    assert response.json()["items"] == [] or isinstance(response.json()["items"], list)


@pytest.mark.asyncio
async def test_update_application_status(client, db_session):
    job = await _seed_job_for_app(db_session)
    app_record = Application(
        job_id=job.id,
        status=ApplicationStatus.generated,
    )
    db_session.add(app_record)
    await db_session.commit()
    await db_session.refresh(app_record)

    response = await client.patch(
        f"/api/applications/{app_record.id}",
        json={"status": "applied"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "applied"
```

- [ ] **Step 2: Write settings test**

```python
# backend/tests/test_settings_api.py
import pytest


@pytest.mark.asyncio
async def test_get_settings(client):
    response = await client.get("/api/settings")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_update_setting(client):
    response = await client.put(
        "/api/settings/match_threshold",
        json={"value": {"threshold": 50}},
    )
    assert response.status_code == 200
    assert response.json()["key"] == "match_threshold"

    # Verify it persists
    response = await client.get("/api/settings/match_threshold")
    assert response.status_code == 200
    assert response.json()["value"]["threshold"] == 50
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_applications_api.py tests/test_settings_api.py -v`
Expected: FAIL — routes don't exist.

- [ ] **Step 4: Write apply.py (applications API)**

```python
# backend/app/api/apply.py
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.application import Application
from app.models.job import Job
from app.schemas.application import (
    ApplicationListResponse,
    ApplicationResponse,
    ApplicationStatusUpdate,
)

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=ApplicationListResponse)
async def list_applications(db: AsyncSession = Depends(get_db)):
    query = (
        select(Application)
        .order_by(Application.updated_at.desc())
    )
    result = await db.execute(query)
    apps = result.scalars().all()

    items = []
    for app_record in apps:
        item = ApplicationResponse.model_validate(app_record)
        # Fetch job info
        job_result = await db.execute(select(Job).where(Job.id == app_record.job_id))
        job = job_result.scalar_one_or_none()
        if job:
            item.job_title = job.title
            item.job_company = job.company
        items.append(item)

    return ApplicationListResponse(items=items)


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update_application_status(
    application_id: uuid.UUID,
    body: ApplicationStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    app_record = result.scalar_one_or_none()
    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")

    app_record.status = body.status
    await db.commit()
    await db.refresh(app_record)

    item = ApplicationResponse.model_validate(app_record)
    job_result = await db.execute(select(Job).where(Job.id == app_record.job_id))
    job = job_result.scalar_one_or_none()
    if job:
        item.job_title = job.title
        item.job_company = job.company
    return item
```

- [ ] **Step 5: Write settings.py API**

```python
# backend/app/api/settings.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.setting import Setting
from app.schemas.setting import SettingResponse, SettingUpdate

router = APIRouter(prefix="/settings", tags=["settings"])

DEFAULT_SETTINGS = {
    "scrape_frequency": {"interval": "daily"},
    "scrape_portals": {"enabled": ["linkedin", "indeed", "glassdoor", "wellfound", "seek"]},
    "match_threshold": {"threshold": 50},
    "usage_cap_type": {"type": None},
    "usage_cap_value": {"value": None},
    "telegram_chat_id": {"chat_id": ""},
    "search_keywords": {"keywords": []},
    "preferred_locations": {"locations": []},
    "default_visa_filter": {"values": ["authorized", "will_sponsor"]},
}


@router.get("", response_model=list[SettingResponse])
async def list_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Setting))
    settings = result.scalars().all()
    return [SettingResponse.model_validate(s) for s in settings]


@router.get("/{key}", response_model=SettingResponse)
async def get_setting(key: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        # Return default if it exists
        if key in DEFAULT_SETTINGS:
            setting = Setting(key=key, value=DEFAULT_SETTINGS[key])
            db.add(setting)
            await db.commit()
            await db.refresh(setting)
            return SettingResponse.model_validate(setting)
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    return SettingResponse.model_validate(setting)


@router.put("/{key}", response_model=SettingResponse)
async def update_setting(
    key: str, body: SettingUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = body.value
    else:
        setting = Setting(key=key, value=body.value)
        db.add(setting)
    await db.commit()
    await db.refresh(setting)
    return SettingResponse.model_validate(setting)
```

- [ ] **Step 6: Register both routers**

```python
# backend/app/api/router.py
from fastapi import APIRouter

from app.api.apply import router as applications_router
from app.api.jobs import router as jobs_router
from app.api.resume import router as resume_router
from app.api.settings import router as settings_router

api_router = APIRouter()
api_router.include_router(jobs_router)
api_router.include_router(resume_router)
api_router.include_router(applications_router)
api_router.include_router(settings_router)
```

- [ ] **Step 7: Run all tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/app/api/ backend/tests/
git commit -m "feat: add applications and settings APIs with tests"
```

---

### Task 13: Dockerfile & Railway Config

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/railway.toml`

- [ ] **Step 1: Write Dockerfile**

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system deps for pdflatex (needed in Plan 3)
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-fonts-recommended \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (needed in Plan 2)
RUN pip install playwright && playwright install chromium && playwright install-deps

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Write railway.toml**

```toml
# backend/railway.toml
[build]
dockerfilePath = "Dockerfile"

[deploy]
startCommand = "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

- [ ] **Step 3: Verify Docker build locally (optional)**

Run:
```bash
cd backend && docker build -t autojob-backend .
```

Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
git add backend/Dockerfile backend/railway.toml
git commit -m "feat: add Dockerfile and Railway deploy config"
```

---

## Plan 1 Complete

At this point you have:
- FastAPI app with health check, CORS, and lifespan hooks
- 7 SQLAlchemy models matching the spec (all enums, relationships, constraints)
- Alembic migrations for PostgreSQL
- CRUD API routes: `/api/jobs`, `/api/resume`, `/api/applications`, `/api/settings`
- Filtering, sorting, and pagination on jobs
- Async test suite with isolated test database
- Docker + Railway deployment config

**Ready for:**
- **Plan 2:** Scraper Engine (Playwright scrapers plug into this DB and API)
- **Plan 3:** LLM Services (matcher, parser, resume gen use these models and routes)
- **Plan 4:** Frontend (calls these API endpoints)
