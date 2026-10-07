import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
@pytest.mark.skip(reason='Needs update')
async def test_voice_agent_and_dashboard(client: AsyncClient):
    # 1. Register elder
    reg = await client.post(
        "/api/auth/register",
        json={"email": "elder_voice@example.com", "password": "StrongPassword1!", "role": "ELDER", "full_name": "Grandpa Joe"}
    )
    assert reg.status_code == 200
    elder_id = reg.json()["id"]

    # 2. Login
    login = await client.post("/api/auth/login", data={"username": "elder_voice@example.com", "password": "StrongPassword1!"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Trigger Outbound Call
    call_res = await client.post(
        "/api/voice/outbound-call",
        headers=headers,
        json={"elder_id": elder_id, "call_type": "OUTBOUND_CHECKIN"}
    )
    assert call_res.status_code == 200
    assert call_res.json()["status"] == "COMPLETED"

    # 4. Trigger SOS activity (Policy engine generates alert)
    sos_res = await client.post(f"/api/elders/{elder_id}/sos", headers=headers)
    assert sos_res.status_code == 200

    # 5. Fetch Caregiver Dashboard Overview
    dash_res = await client.get(f"/api/dashboard/overview/{elder_id}", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["elder_name"] == "Grandpa Joe"
    assert dash_data["status_badge"] == "SOS_ALERT"
    assert dash_data["active_alerts_count"] >= 1

    # 6. Fetch Alerts and resolve
    alerts_res = await client.get(f"/api/alerts/{elder_id}", headers=headers)
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) >= 1
    alert_id = alerts[0]["id"]

    resolve_res = await client.put(f"/api/alerts/{alert_id}/resolve", headers=headers)
    assert resolve_res.status_code == 200
    assert resolve_res.json()["is_resolved"] is True
