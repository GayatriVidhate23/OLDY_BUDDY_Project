import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone

@pytest.mark.asyncio
@pytest.mark.skip(reason='Needs update')
async def test_module5_sos_escalation(client: AsyncClient):
    # 1. Register elder
    eld_reg = await client.post("/api/auth/register", json={"email": "elder_mod5@example.com", "password": "StrongPassword1!", "role": "ELDER"})
    login = await client.post("/api/auth/login", data={"username": "elder_mod5@example.com", "password": "StrongPassword1!"})
    eld_token = login.json()["access_token"]
    headers_eld = {"Authorization": f"Bearer {eld_token}"}
    elder_id = eld_reg.json()["id"]

    # 2. Register caregiver
    cg_reg = await client.post("/api/auth/register", json={"email": "cg_mod5@example.com", "password": "StrongPassword1!", "role": "CAREGIVER"})
    login_cg = await client.post("/api/auth/login", data={"username": "cg_mod5@example.com", "password": "StrongPassword1!"})
    cg_token = login_cg.json()["access_token"]
    headers_cg = {"Authorization": f"Bearer {cg_token}"}
    cg_id = cg_reg.json()["id"]

    # 3. Link caregiver to elder directly in DB via API (if we have caregiver adding endpoint, but wait we need auth)
    # Actually, we can just use the DB to link, or use the endpoint. Module 2 has POST /v1/elders/{elder_id}/caregivers but it's protected.
    # Let's just create an elder from caregiver's side so it links automatically.
    
    eld2_req = {
        "name": "Module5 Elder",
        "phone_e164": "+9876543210",
        "language_code": "en-IN"
    }
    eld2_res = await client.post("/api/elders", headers=headers_cg, json=eld2_req)
    elder2_id = eld2_res.json()["user_id"]

    # We need to authenticate elder2 to trigger SOS. We can pair it.
    pair_res = await client.post(f"/api/elders/{elder2_id}/pairing-code", headers=headers_cg)
    code = pair_res.json()["code"]
    auth_pair = await client.post("/api/auth/pair", json={"code": code})
    eld2_token = auth_pair.json()["access_token"]
    headers_eld2 = {"Authorization": f"Bearer {eld2_token}"}

    # 4. Trigger SOS as elder
    sos_res = await client.post("/api/sos", headers=headers_eld2)
    assert sos_res.status_code == 200
    alert_id = sos_res.json()["alert_id"]
    assert alert_id is not None

    # 5. Check duplicate SOS (should not create another alert)
    sos_res2 = await client.post("/api/sos", headers=headers_eld2)
    alert2_id = sos_res2.json()["alert_id"]
    assert alert2_id is None # decision_engine suppresses duplicate

    # 6. Verify SOS Safe (Elder)
    ver_res = await client.post(f"/api/alerts/{alert_id}/verify", headers=headers_eld2, json={"safe": True})
    assert ver_res.status_code == 200

    # Check alert is resolved
    al_res = await client.get(f"/api/elders/{elder2_id}/alerts?status=resolved", headers=headers_cg)
    assert len(al_res.json()) >= 1
    assert al_res.json()[0]["status"] == "resolved"

    # 7. Trigger another SOS
    sos_res3 = await client.post("/api/sos", headers=headers_eld2)
    alert3_id = sos_res3.json()["alert_id"]
    
    # 8. Unsafe verification
    ver_res2 = await client.post(f"/api/alerts/{alert3_id}/verify", headers=headers_eld2, json={"safe": False})
    
    # 9. Caregiver Acknowledges
    ack_res = await client.post(f"/api/alerts/{alert3_id}/ack", headers=headers_cg)
    assert ack_res.status_code == 200

    # 10. List events
    ev_res = await client.get(f"/api/elders/{elder2_id}/events", headers=headers_cg)
    assert ev_res.status_code == 200
    events = ev_res.json()
    types = [e["event_type"] for e in events]
    assert "sos_pressed" in types
    assert "sos_cancelled" in types
    assert "alert_acknowledged" in types

@pytest.mark.asyncio
async def test_decision_engine_rules(client: AsyncClient):
    pass
