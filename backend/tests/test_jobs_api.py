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


@pytest.mark.asyncio(loop_scope="session")
async def test_list_jobs_empty(client):
    response = await client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["items"], list)


@pytest.mark.asyncio(loop_scope="session")
async def test_list_jobs_returns_seeded_job(client, db_session):
    job = await _seed_job(db_session)
    response = await client.get("/api/jobs?show_all=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    titles = [j["title"] for j in data["items"]]
    assert "Software Engineer" in titles


@pytest.mark.asyncio(loop_scope="session")
async def test_filter_by_portal(client, db_session):
    await _seed_job(db_session, portal=Portal.linkedin, external_id="ln-filter")
    await _seed_job(db_session, portal=Portal.seek, external_id="sk-filter")
    response = await client.get("/api/jobs?portal=linkedin&show_all=true")
    assert response.status_code == 200
    data = response.json()
    for job in data["items"]:
        assert job["portal"] == "linkedin"


@pytest.mark.asyncio(loop_scope="session")
async def test_get_job_by_id(client, db_session):
    job = await _seed_job(db_session, external_id="get-test")
    response = await client.get(f"/api/jobs/{job.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(job.id)


@pytest.mark.asyncio(loop_scope="session")
async def test_get_job_not_found(client):
    fake_id = uuid.uuid4()
    response = await client.get(f"/api/jobs/{fake_id}")
    assert response.status_code == 404
