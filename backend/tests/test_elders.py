import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
@pytest.mark.skip(reason='Needs update')
async def test_elder_profile(client: AsyncClient):
    # Register an elder
    reg = await client.post(
        "/api/auth/register",
        json={"email": "elder1@example.com", "password": "StrongPassword1!", "role": "ELDER"}
    )
    assert reg.status_code == 200
    elder_id = reg.json()["id"]

    # Login
    login = await client.post(
        "/api/auth/login", data={"username": "elder1@example.com", "password": "StrongPassword1!"}
    )
    token = login.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Update profile
    prof_update = await client.put(
        f"/api/elders/{elder_id}",
        headers=headers,
        json={"emergency_contact": "911-CONTACT"}
    )
    assert prof_update.status_code == 200
    assert prof_update.json()["emergency_contact"] == "911-CONTACT"
    
    # Get profile
    prof_get = await client.get(
        f"/api/elders/{elder_id}",
        headers=headers
    )
    assert prof_get.status_code == 200
    assert prof_get.json()["user_id"] == elder_id
