import io
import pytest


@pytest.mark.asyncio(loop_scope="session")
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


@pytest.mark.asyncio(loop_scope="session")
async def test_get_active_resume(client):
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake pdf content")
    await client.post(
        "/api/resume/upload",
        files={"file": ("active.pdf", fake_pdf, "application/pdf")},
    )
    response = await client.get("/api/resume/active")
    assert response.status_code == 200
    assert response.json()["file_name"] == "active.pdf"


@pytest.mark.asyncio(loop_scope="session")
async def test_list_resumes(client):
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake pdf content")
    await client.post(
        "/api/resume/upload",
        files={"file": ("list_test.pdf", fake_pdf, "application/pdf")},
    )
    response = await client.get("/api/resume")
    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1
