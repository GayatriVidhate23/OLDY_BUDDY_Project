import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password", "role": "ELDER", "full_name": "Test User"}
    )
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "test2@example.com", "password": "password", "role": "ELDER", "full_name": "Test User"}
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test2@example.com", "password": "password"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()

@pytest.mark.asyncio
async def test_admin_registration_rejected(client: AsyncClient):
    res = await client.post("/api/auth/register", json={"email": "admin@test.com", "password": "StrongPassword1!", "role": "ADMIN"})
    assert res.status_code in [403, 400]

@pytest.mark.asyncio
async def test_password_policy(client: AsyncClient):
    res = await client.post("/api/auth/register", json={"email": "weak@test.com", "password": "123", "role": "ELDER"})
    assert res.status_code in [422, 400]
    
    res2 = await client.post("/api/auth/register", json={"email": "good@test.com", "password": "StrongPassword1!", "role": "ELDER"})
    assert res2.status_code in [200, 201]

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
    login = await client.post("/api/auth/login/form", data={"username": "tok_unique@test.com", "password": "StrongPassword1!"})
    
    access = login.json()["access_token"]
    refresh = login.json()["refresh_token"]
    
    res = await client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert res.status_code == 200
    new_access = res.json()["access_token"]
    new_refresh = res.json()["refresh_token"]

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
    u1 = await client.post("/api/auth/register", json={"email": "elder1@test.com", "password": "StrongPassword1!", "role": "ELDER"})
    e1_id = u1.json()["id"]
    l1 = await client.post("/api/auth/login/form", data={"username": "elder1@test.com", "password": "StrongPassword1!"})
    t1 = l1.json()["access_token"]
    
    u2 = await client.post("/api/auth/register", json={"email": "elder2@test.com", "password": "StrongPassword1!", "role": "ELDER"})
    e2_id = u2.json()["id"]
    
    res = await client.get(f"/api/v1/elders/{e2_id}", headers={"Authorization": f"Bearer {t1}"})
    assert res.status_code in [403, 404]
