import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
@pytest.mark.skip(reason='Needs update')
async def test_auth_and_profile(client: AsyncClient):
    reg = await client.post("/api/auth/register", json={"email": "test@example.com", "password": "StrongPassword1!", "role": "ELDER"})
    assert reg.status_code in [200, 201]
    elder_id = reg.json()["id"]

    login = await client.post("/api/auth/login", data={"username": "test@example.com", "password": "StrongPassword1!"})
    token = login.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    prof_create = await client.post(f"/api/elders/{elder_id}/profile", headers=headers, json={"emergency_contact": "911"})
    assert prof_create.status_code == 200

    act = await client.post(f"/api/elders/{elder_id}/activities", headers=headers, json={"activity_type": "SOS", "description": "Help!"})
    assert act.status_code in [200, 201]
