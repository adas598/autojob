from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.job import Job


async def _create_job(db_engine) -> str:
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        job = Job(title="Dev", company="Corp", url="https://seek.com/701", source="seek")
        session.add(job)
        await session.commit()
        return job.id


async def test_list_applied_history_empty(client):
    response = await client.get("/applied-history/")
    assert response.status_code == 200
    assert response.json() == []


async def test_create_applied_history(client, db_engine):
    job_id = await _create_job(db_engine)
    response = await client.post(
        "/applied-history/",
        json={"job_id": job_id, "status": "applied", "notes": "Applied via SEEK"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "applied"
    assert data["job_id"] == job_id


async def test_list_applied_history_filter_by_job(client, db_engine):
    job_id = await _create_job(db_engine)
    await client.post("/applied-history/", json={"job_id": job_id, "status": "applied"})
    response = await client.get(f"/applied-history/?job_id={job_id}")
    assert len(response.json()) == 1


async def test_update_applied_history_status(client, db_engine):
    job_id = await _create_job(db_engine)
    r = await client.post("/applied-history/", json={"job_id": job_id, "status": "applied"})
    entry_id = r.json()["id"]
    response = await client.patch(
        f"/applied-history/{entry_id}",
        json={"status": "interview", "notes": "Phone screen booked"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "interview"


async def test_update_applied_history_not_found(client):
    response = await client.patch("/applied-history/bad-id", json={"status": "offer"})
    assert response.status_code == 404
