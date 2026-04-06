from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models import Base, Job, Profile, Application, Source, AppliedHistory
from app.models.job import JobStatus, MatchScore
from app.models.source import SourceType
from app.models.applied_history import ApplicationStatus

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


async def make_session():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def test_profile_creates():
    engine, factory = await make_session()
    async with factory() as s:
        profile = Profile(id=1, name="Jane Doe", email="jane@example.com")
        s.add(profile)
        await s.commit()
        result = await s.get(Profile, 1)
        assert result.name == "Jane Doe"
    await engine.dispose()


async def test_job_creates():
    engine, factory = await make_session()
    async with factory() as s:
        job = Job(title="Software Engineer", company="Acme", url="https://seek.com/1", source="seek")
        s.add(job)
        await s.commit()
        result = await s.get(Job, job.id)
        assert result.status == JobStatus.pending
        assert result.match_score is None
    await engine.dispose()


async def test_application_creates():
    engine, factory = await make_session()
    async with factory() as s:
        job = Job(title="Dev", company="Corp", url="https://seek.com/2", source="seek")
        s.add(job)
        await s.commit()
        app = Application(job_id=job.id, cover_letter="Dear Hiring Manager...")
        s.add(app)
        await s.commit()
        result = await s.get(Application, app.id)
        assert result.cover_letter == "Dear Hiring Manager..."
    await engine.dispose()


async def test_source_creates():
    engine, factory = await make_session()
    async with factory() as s:
        source = Source(type=SourceType.portal, name="SEEK", url="https://seek.com.au")
        s.add(source)
        await s.commit()
        result = await s.get(Source, source.id)
        assert result.enabled is True
    await engine.dispose()


async def test_applied_history_creates():
    engine, factory = await make_session()
    async with factory() as s:
        job = Job(title="Dev", company="Corp", url="https://seek.com/3", source="seek")
        s.add(job)
        await s.commit()
        entry = AppliedHistory(job_id=job.id, status=ApplicationStatus.applied)
        s.add(entry)
        await s.commit()
        result = await s.get(AppliedHistory, entry.id)
        assert result.status == ApplicationStatus.applied
    await engine.dispose()
