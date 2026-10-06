import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_admin_registration_rejected(client: AsyncClient):
    res = await client.post("/api/auth/register", json={"email": "admin@test.com", "password": "StrongPassword1!", "role": "ADMIN"})
    assert res.status_code in [403, 400]

@pytest.mark.asyncio
async def test_password_policy(client: AsyncClient):
    res = await client.post("/api/auth/register", json={"email": "weak@test.com", "password": "weak", "role": "ELDER"})
    assert res.status_code == 422 # FastAPI Pydantic validation error
    
    res2 = await client.post("/api/auth/register", json={"email": "good@test.com", "password": "StrongPassword1!", "role": "ELDER"})
    assert res2.status_code == 200

@pytest.mark.asyncio
async def test_duplicate_user(client: AsyncClient):
    await client.post("/api/auth/register", json={"email": "dup@test.com", "password": "StrongPassword1!", "role": "ELDER"})
    res = await client.post("/api/auth/register", json={"email": "dup@test.com", "password": "StrongPassword2!", "role": "ELDER"})
    assert res.status_code == 400

@pytest.mark.asyncio
async def test_invalid_token(client: AsyncClient):
    res = await client.get("/api/auth/me", headers={"Authorization": "Bearer badtoken"})
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_refresh_token_lifecycle(client: AsyncClient):
    await client.post("/api/auth/register", json={"email": "tok_unique@test.com", "password": "StrongPassword1!", "role": "ELDER"})
    login = await client.post("/api/auth/login", data={"username": "tok_unique@test.com", "password": "StrongPassword1!"})
    
    access = login.json()["access_token"]
    refresh = login.json()["refresh_token"]
    
    # Test valid refresh
    res = await client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert res.status_code == 200
    new_access = res.json()["access_token"]
    new_refresh = res.json()["refresh_token"]
    
    # Test old refresh is revoked
    res_fail = await client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert res_fail.status_code == 401
    
    # Test logout
    logout_res = await client.post("/api/auth/logout", json={"refresh_token": new_refresh})
    assert logout_res.status_code == 200
    
    res_fail_2 = await client.post("/api/auth/refresh", json={"refresh_token": new_refresh})
    assert res_fail_2.status_code == 401

@pytest.mark.asyncio
async def test_otp_flow(client: AsyncClient):
    await client.post("/api/auth/register", json={"email": "otp@test.com", "password": "StrongPassword1!", "role": "ELDER"})
    
    req_res = await client.post("/api/auth/request-otp", json={"email": "otp@test.com"})
    assert req_res.status_code == 200
    
    ver_fail = await client.post("/api/auth/verify-otp", json={"email": "otp@test.com", "code": "999999"})
    assert ver_fail.status_code == 400
    
    ver_ok = await client.post("/api/auth/verify-otp", json={"email": "otp@test.com", "code": "123456"})
    assert ver_ok.status_code == 200
    assert "access_token" in ver_ok.json()

@pytest.mark.asyncio
async def test_authorization(client: AsyncClient):
    # Elder 1
    u1 = await client.post("/api/auth/register", json={"email": "elder1@test.com", "password": "StrongPassword1!", "role": "ELDER"})
    e1_id = u1.json()["id"]
    l1 = await client.post("/api/auth/login", data={"username": "elder1@test.com", "password": "StrongPassword1!"})
    t1 = l1.json()["access_token"]
    
    # Elder 2
    u2 = await client.post("/api/auth/register", json={"email": "elder2@test.com", "password": "StrongPassword1!", "role": "ELDER"})
    e2_id = u2.json()["id"]
    
    # Elder 1 accessing Elder 2's data
    res = await client.get(f"/api/elders/{e2_id}/profile", headers={"Authorization": f"Bearer {t1}"})
    assert res.status_code == 403
