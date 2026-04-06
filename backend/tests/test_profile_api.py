async def test_get_profile_returns_default(client):
    response = await client.get("/profile/")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == ""
    assert data["work_rights"] == "Full work rights"


async def test_update_profile(client):
    response = await client.put(
        "/profile/",
        json={"name": "Jane Doe", "email": "jane@example.com", "skills": ["Python", "SQL"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["skills"] == ["Python", "SQL"]


async def test_update_profile_partial(client):
    await client.put("/profile/", json={"name": "Jane"})
    response = await client.put("/profile/", json={"email": "jane@example.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jane"
    assert data["email"] == "jane@example.com"
