import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_elder_profile(client: AsyncClient):
    # Register an elder
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "elder1@example.com", "password": "pass", "role": "ELDER"}
    )
    assert reg.status_code == 200
    elder_id = reg.json()["id"]

    # Login
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "elder1@example.com", "password": "pass"}
    )
    token = login.json()["access_token"]
    
    # Create profile
    headers = {"Authorization": f"Bearer {token}"}
    prof_create = await client.post(
        f"/api/v1/elders/{elder_id}/profile",
        headers=headers,
        json={"user_id": elder_id, "emergency_contact": "911"}
    )
    assert prof_create.status_code == 200
    assert prof_create.json()["emergency_contact"] == "911"
    
    # Get profile
    prof_get = await client.get(
        f"/api/v1/elders/{elder_id}/profile",
        headers=headers
    )
    assert prof_get.status_code == 200
