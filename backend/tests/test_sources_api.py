async def test_list_sources_empty(client):
    response = await client.get("/sources/")
    assert response.status_code == 200
    assert response.json() == []


async def test_create_source(client):
    response = await client.post(
        "/sources/",
        json={"type": "portal", "name": "SEEK", "url": "https://seek.com.au"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "SEEK"
    assert data["enabled"] is True


async def test_list_sources_after_create(client):
    await client.post("/sources/", json={"type": "portal", "name": "SEEK", "url": ""})
    response = await client.get("/sources/")
    assert len(response.json()) == 1


async def test_toggle_source_disabled(client):
    r = await client.post(
        "/sources/",
        json={"type": "company", "name": "Atlassian", "url": "https://atlassian.com/careers"},
    )
    source_id = r.json()["id"]
    response = await client.patch(f"/sources/{source_id}", json={"enabled": False})
    assert response.status_code == 200
    assert response.json()["enabled"] is False


async def test_delete_source(client):
    r = await client.post("/sources/", json={"type": "portal", "name": "Temp", "url": ""})
    source_id = r.json()["id"]
    response = await client.delete(f"/sources/{source_id}")
    assert response.status_code == 204
    list_response = await client.get("/sources/")
    assert list_response.json() == []


async def test_delete_source_not_found(client):
    response = await client.delete("/sources/bad-id")
    assert response.status_code == 404
