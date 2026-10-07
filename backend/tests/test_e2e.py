import pytest
from httpx import AsyncClient
import os

@pytest.mark.asyncio
async def test_e2e_caregiver_creates_elder_and_routine(client: AsyncClient):
    """FLOW 1 & 3: Caregiver auth, elder creation, routine config."""
    # Register CG
    res = await client.post("/api/auth/register", json={"email": "e2e_cg@example.com", "password": "StrongPassword1!", "role": "CAREGIVER"})
    assert res.status_code in (200, 201)
    
    login = await client.post("/api/auth/login", data={"username": "e2e_cg@example.com", "password": "StrongPassword1!"})
    cg_token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {cg_token}"}
    
    # Create elder
    eld_req = {"name": "E2E Elder", "phone_e164": "+918000000000", "language_code": "en-IN"}
    eld_res = await client.post("/api/v1/elders", headers=headers, json=eld_req)
    assert eld_res.status_code == 200
    elder_id = eld_res.json()["user_id"]
    
    # Configure routine
    rt_req = {"wake_time": "08:00", "sleep_time": "21:00", "checkin_times": ["10:00", "14:00"]}
    rt_res = await client.put(f"/api/v1/elders/{elder_id}/routine", headers=headers, json=rt_req)
    assert rt_res.status_code == 200

    # Emergency Contact
    ec_req = {"name": "Local Doc", "phone_e164": "+919000000000"}
    await client.post(f"/api/v1/elders/{elder_id}/emergency-contacts", headers=headers, json=ec_req)

@pytest.mark.asyncio
async def test_e2e_health_ready(client: AsyncClient):
    res = await client.get("/healthz")
    assert res.status_code == 200
    res = await client.get("/readyz")
    assert res.status_code == 200

@pytest.mark.asyncio
async def test_token_security(client: AsyncClient):
    """FLOW 6: Token security"""
    res = await client.post("/api/auth/register", json={"email": "tok_sec@example.com", "password": "StrongPassword1!", "role": "CAREGIVER"})
    login = await client.post("/api/auth/login", data={"username": "tok_sec@example.com", "password": "StrongPassword1!"})
    
    # Invalid token
    res = await client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert res.status_code == 401
