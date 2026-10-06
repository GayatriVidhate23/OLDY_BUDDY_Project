
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_voice_checkin_flow(client: AsyncClient):
    # Register Elder
    reg = await client.post("/api/auth/register", json={"email": "elder_voice@example.com", "password": "StrongPassword1!", "role": "ELDER"})
    elder_id = reg.json()["id"]

    # Trigger Outbound Call
    outbound = await client.post("/api/voice/outbound", json={"elder_id": elder_id, "call_type": "CHECK_IN"})
    assert outbound.status_code == 200
    call_id = outbound.json()["id"]

    # Webhook: Call Answered
    ans = await client.post("/api/voice/webhook", json={"call_id": call_id, "event_type": "answered"})
    assert ans.status_code == 200

    # Webhook: Speech YES
    sp_yes = await client.post("/api/voice/webhook", json={"call_id": call_id, "event_type": "speech", "speech_text": "Yes I did"})
    assert sp_yes.json()["record"]["response"] == "YES"

@pytest.mark.asyncio
async def test_voice_sos_flow(client: AsyncClient):
    reg = await client.post("/api/auth/register", json={"email": "elder_sos@example.com", "password": "StrongPassword1!", "role": "ELDER"})
    elder_id = reg.json()["id"]
    
    login = await client.post("/api/auth/login", data={"username": "elder_sos@example.com", "password": "StrongPassword1!"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    outbound = await client.post("/api/voice/outbound", json={"elder_id": elder_id, "call_type": "REMINDER"})
    call_id = outbound.json()["id"]

    # Elder says I need help
    sp_help = await client.post("/api/voice/webhook", json={"call_id": call_id, "event_type": "speech", "speech_text": "I need help please"})
    assert sp_help.status_code == 200
    assert sp_help.json()["record"]["response"] == "NEED_HELP"

    # Verify Activity SOS was created
    acts = await client.get(f"/api/elders/{elder_id}/activities", headers=headers)
    sos_act = [a for a in acts.json() if a["activity_type"] == "SOS"]
    assert len(sos_act) > 0
