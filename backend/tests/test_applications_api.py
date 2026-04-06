from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.application import Application
from app.models.job import Job


async def _seed(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        job = Job(title="Dev", company="Corp", url="https://seek.com/601", source="seek")
        session.add(job)
        await session.flush()
        app = Application(
            job_id=job.id,
            cover_letter="Dear Hiring Manager,",
            application_answers={"q1": "answer1"},
        )
        session.add(app)
        await session.commit()
        return job.id, app.id


async def test_list_applications_empty(client):
    response = await client.get("/applications/")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_applications(client, db_engine):
    await _seed(db_engine)
    response = await client.get("/applications/")
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_get_application_by_id(client, db_engine):
    _, app_id = await _seed(db_engine)
    response = await client.get(f"/applications/{app_id}")
    assert response.status_code == 200
    assert response.json()["cover_letter"] == "Dear Hiring Manager,"


async def test_get_application_not_found(client):
    response = await client.get("/applications/bad-id")
    assert response.status_code == 404


async def test_update_application_cover_letter(client, db_engine):
    _, app_id = await _seed(db_engine)
    response = await client.patch(
        f"/applications/{app_id}",
        json={"cover_letter": "Updated cover letter."},
    )
    assert response.status_code == 200
    assert response.json()["cover_letter"] == "Updated cover letter."


async def test_filter_applications_by_job_id(client, db_engine):
    job_id, _ = await _seed(db_engine)
    response = await client.get(f"/applications/?job_id={job_id}")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["job_id"] == job_id
