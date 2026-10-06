import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
@pytest.mark.skip(reason='Needs update')
async def test_create_sos_activity(client: AsyncClient):
    reg = await client.post("/api/auth/register", json={"email": "elder_act@example.com", "password": "StrongPassword1!", "role": "ELDER"})
    elder_id = reg.json()["id"]
    login = await client.post("/api/auth/login", data={"username": "elder_act@example.com", "password": "StrongPassword1!"})
    token = login.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    act = await client.post(
        f"/api/elders/{elder_id}/activities",
        headers=headers,
        json={"activity_type": "SOS", "description": "Fallen down"}
    )
    assert act.status_code == 200
    assert act.json()["activity_type"] == "SOS"

@pytest.mark.asyncio
@pytest.mark.skip(reason='Needs update')
async def test_checkin_and_sos_shortcuts(client: AsyncClient):
    reg = await client.post("/api/auth/register", json={"email": "elder_shortcuts@example.com", "password": "StrongPassword1!", "role": "ELDER"})
    elder_id = reg.json()["id"]
    login = await client.post("/api/auth/login", data={"username": "elder_shortcuts@example.com", "password": "StrongPassword1!"})
    token = login.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    checkin = await client.post(f"/api/elders/{elder_id}/check-in", headers=headers)
    assert checkin.status_code == 200
    assert checkin.json()["activity_type"] == "CHECK_IN"

    sos = await client.post(f"/api/elders/{elder_id}/sos", headers=headers)
    assert sos.status_code == 200
    assert sos.json()["activity_type"] == "SOS"
