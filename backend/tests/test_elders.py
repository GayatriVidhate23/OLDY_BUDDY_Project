import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_elder_profile(client: AsyncClient):
    # Register an elder
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "elder1@example.com", "password": "pass", "role": "ELDER"}
    )
    assert reg.status_code == 201
    elder_id = reg.json()["id"]

    # Login
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "elder1@example.com", "password": "pass"}
    )
    token = login.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Update profile
    prof_update = await client.put(
        f"/api/v1/elders/{elder_id}",
        headers=headers,
        json={"emergency_contact": "911-CONTACT"}
    )
    assert prof_update.status_code == 200
    assert prof_update.json()["emergency_contact"] == "911-CONTACT"
    
    # Get profile
    prof_get = await client.get(
        f"/api/v1/elders/{elder_id}",
        headers=headers
    )
    assert prof_get.status_code == 200
    assert prof_get.json()["user_id"] == elder_id
