import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_get_settings(client):
    response = await client.get("/api/settings")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio(loop_scope="session")
async def test_update_setting(client):
    response = await client.put(
        "/api/settings/match_threshold",
        json={"value": {"threshold": 50}},
    )
    assert response.status_code == 200
    assert response.json()["key"] == "match_threshold"

    response = await client.get("/api/settings/match_threshold")
    assert response.status_code == 200
    assert response.json()["value"]["threshold"] == 50
