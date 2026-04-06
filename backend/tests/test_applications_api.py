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


@pytest.mark.asyncio(loop_scope="session")
async def test_list_applications_empty(client):
    response = await client.get("/api/applications")
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


@pytest.mark.asyncio(loop_scope="session")
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
