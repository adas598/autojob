from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.job import Job, JobStatus, MatchScore


async def _create_job(session: AsyncSession, **kwargs) -> Job:
    defaults = {
        "title": "Software Engineer",
        "company": "Acme",
        "url": f"https://seek.com/{id(kwargs)}",
        "source": "seek",
    }
    job = Job(**{**defaults, **kwargs})
    session.add(job)
    await session.commit()
    return job


async def test_list_jobs_empty(client):
    response = await client.get("/jobs/")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_jobs_returns_jobs(client, db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        await _create_job(session, url="https://seek.com/101")
        await _create_job(session, url="https://seek.com/102")

    response = await client.get("/jobs/")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_list_jobs_filter_by_status(client, db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        await _create_job(session, url="https://seek.com/201", status=JobStatus.approved)
        await _create_job(session, url="https://seek.com/202", status=JobStatus.rejected)

    response = await client.get("/jobs/?status=approved")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "approved"


async def test_list_jobs_filter_by_match_score(client, db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        await _create_job(session, url="https://seek.com/301", match_score=MatchScore.strong)
        await _create_job(session, url="https://seek.com/302", match_score=MatchScore.weak)

    response = await client.get("/jobs/?match_score=strong")
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_get_job_by_id(client, db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        job = await _create_job(session, url="https://seek.com/401", title="Backend Dev")

    response = await client.get(f"/jobs/{job.id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Backend Dev"


async def test_get_job_not_found(client):
    response = await client.get("/jobs/nonexistent-id")
    assert response.status_code == 404


async def test_update_job_status(client, db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        job = await _create_job(session, url="https://seek.com/501")

    response = await client.patch(
        f"/jobs/{job.id}/status", json={"status": "approved"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


async def test_update_job_status_not_found(client):
    response = await client.patch("/jobs/bad-id/status", json={"status": "approved"})
    assert response.status_code == 404
