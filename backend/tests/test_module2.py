import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_module2(client: AsyncClient):
    # 1. Register caregiver
    cg_reg = await client.post("/api/auth/register", json={"email": "cg_mod2@example.com", "password": "StrongPassword1!", "role": "CAREGIVER"})
    assert cg_reg.status_code in (200, 201)
    
    login = await client.post("/api/auth/login", data={"username": "cg_mod2@example.com", "password": "StrongPassword1!"})
    cg_token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {cg_token}"}
    
    # 2. Caregiver creates elder
    eld_req = {
        "name": "Module2 Elder",
        "phone_e164": "+1234567890",
        "language_code": "hi-IN",
        "tts_speaker": "speaker_1"
    }
    eld_res = await client.post("/api/v1/elders", headers=headers, json=eld_req)
    assert eld_res.status_code == 200
    elder_id = eld_res.json()["user_id"]
    
    # 3. Read/update own elder
    read_res = await client.get(f"/api/v1/elders/{elder_id}", headers=headers)
    assert read_res.status_code == 200, read_res.text
    
    # 4. Duplicate phone
    eld_req2 = {
        "name": "Duplicate Phone",
        "phone_e164": "+1234567890"
    }
    eld_res2 = await client.post("/api/v1/elders", headers=headers, json=eld_req2)
    assert eld_res2.status_code == 400
    
    # 5. Invalid language/tts
    eld_req_inv = {
        "name": "Invalid",
        "language_code": "invalid-lang"
    }
    eld_res_inv = await client.post("/api/v1/elders", headers=headers, json=eld_req_inv)
    assert eld_res_inv.status_code == 422
    
    # 6. Unauthorized access (404)
    # Register another caregiver
    cg2_reg = await client.post("/api/auth/register", json={"email": "cg2@example.com", "password": "StrongPassword1!", "role": "CAREGIVER"})
    login2 = await client.post("/api/auth/login", data={"username": "cg2@example.com", "password": "StrongPassword1!"})
    cg2_token = login2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {cg2_token}"}
    
    unauth_res = await client.get(f"/api/v1/elders/{elder_id}", headers=headers2)
    assert unauth_res.status_code in (403, 404)
    
    # 7. Emergency Contacts
    ec_req = {"name": "Doctor", "phone_e164": "+9999999999"}
    ec_res = await client.post(f"/api/v1/elders/{elder_id}/emergency-contacts", headers=headers, json=ec_req)
    assert ec_res.status_code == 200
    ec_id = ec_res.json()["id"]
    
    # Duplicate EC
    ec_res_dup = await client.post(f"/api/v1/elders/{elder_id}/emergency-contacts", headers=headers, json=ec_req)
    assert ec_res_dup.status_code == 400
    
    # Delete compacts priorities
    del_res = await client.delete(f"/api/v1/elders/{elder_id}/emergency-contacts/{ec_id}", headers=headers)
    assert del_res.status_code == 200
    
    # 8. Routine
    rt_req = {"wake_time": "07:00", "sleep_time": "22:00", "checkin_times": ["09:00", "15:00"]}
    rt_res = await client.put(f"/api/v1/elders/{elder_id}/routine", headers=headers, json=rt_req)
    assert rt_res.status_code == 200
    
    sugg_res = await client.get(f"/api/v1/elders/{elder_id}/routine/suggested-reminders", headers=headers)
    assert sugg_res.status_code == 200
    assert len(sugg_res.json()) == 2
    
    # 9. Consent
    c_req = {"kind": "voice_calls"}
    c_res = await client.post(f"/api/v1/elders/{elder_id}/consents", headers=headers, json=c_req)
    assert c_res.status_code == 200
    
    # 10. Pairing
    pair_res = await client.post(f"/api/v1/elders/{elder_id}/pairing-code", headers=headers)
    assert pair_res.status_code == 200
    code = pair_res.json()["code"]
    
    auth_pair = await client.post("/api/v1/auth/pair", json={"code": code})
    assert auth_pair.status_code == 200
    eld_access = auth_pair.json()["access_token"]
    
    eld_me = await client.get("/api/v1/me/elder", headers={"Authorization": f"Bearer {eld_access}"})
    assert eld_me.status_code == 200
    assert eld_me.json()["user_id"] == elder_id
    
    # Code expired/used
    auth_pair2 = await client.post("/api/v1/auth/pair", json={"code": code})
    assert auth_pair2.status_code == 400
