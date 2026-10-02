import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password", "role": "ELDER", "full_name": "Test User"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    # Registration should already be done if run in order, but let's re-register or ignore 400
    await client.post(
        "/api/v1/auth/register",
        json={"email": "test2@example.com", "password": "password", "role": "ELDER", "full_name": "Test User"}
    )
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test2@example.com", "password": "password"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
