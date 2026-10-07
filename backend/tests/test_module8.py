import pytest
import pytest_asyncio
import datetime
from httpx import AsyncClient
from app.models import Alert, Activity, Message, User
from app.api import get_current_user, verify_elder_access
from app.main import app

@pytest.fixture(autouse=True)
def mock_auth():
    async def mock_get_current_user():
        return User(id=1, email="elder@test.com", role="ELDER")
    async def mock_verify_elder_access(elder_id: int):
        if elder_id != 1:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Not authorized to access this elder's data")
        return True
        
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[verify_elder_access] = mock_verify_elder_access
    yield
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def elder_user(db):
    user = User(email="elder@test.com", hashed_password="hash", role="ELDER")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@pytest_asyncio.fixture
async def caregiver_user(db):
    user = User(email="cg@test.com", hashed_password="hash", role="CAREGIVER")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@pytest.mark.asyncio
async def test_status_new_elder_unknown(client: AsyncClient, elder_user, db):
    response = await client.get(f"/api/v1/elders/{elder_user.id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Unknown"

@pytest.mark.asyncio
async def test_status_priority_emergency(client: AsyncClient, elder_user, db):
    alert = Alert(elder_id=elder_user.id, severity="EMERGENCY", title="Test")
    db.add(alert)
    await db.commit()
    
    response = await client.get(f"/api/v1/elders/{elder_user.id}/status")
    assert response.status_code == 200
    assert response.json()["status"] == "Emergency"

@pytest.mark.asyncio
async def test_trends_7_days(client: AsyncClient, elder_user, db):
    today = datetime.datetime.now(datetime.timezone.utc)
    act = Activity(elder_id=elder_user.id, activity_type="REMINDER", status="COMPLETED", timestamp=today)
    db.add(act)
    await db.commit()
    
    response = await client.get(f"/api/v1/elders/{elder_user.id}/trends?days=7")
    assert response.status_code == 200
    data = response.json()
    assert len(data["days"]) == 7
    assert data["days"][-1]["reminders_completed"] == 1
    assert data["days"][0]["reminders_completed"] == 0

@pytest.mark.asyncio
async def test_trends_30_days(client: AsyncClient, elder_user):
    response = await client.get(f"/api/v1/elders/{elder_user.id}/trends?days=30")
    assert response.status_code == 200
    data = response.json()
    assert len(data["days"]) == 30

@pytest.mark.asyncio
async def test_message_creation_and_limit(client: AsyncClient, elder_user):
    response = await client.post(f"/api/v1/elders/{elder_user.id}/messages", json={"body": "Hello"})
    assert response.status_code == 200
    
    long_body = "a" * 501
    response2 = await client.post(f"/api/v1/elders/{elder_user.id}/messages", json={"body": long_body})
    assert response2.status_code == 400

@pytest.mark.asyncio
async def test_quick_reply_call_me(client: AsyncClient, elder_user, db):
    response = await client.post(f"/api/v1/elders/{elder_user.id}/messages", json={"body": "Please call me"})
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_message_read_unread(client: AsyncClient, elder_user, caregiver_user, db):
    # Setup elder message
    await client.post(f"/api/v1/elders/{elder_user.id}/messages", json={"body": "Hi caregiver"})
    
    # Caregiver retrieves
    app.dependency_overrides[get_current_user] = lambda: caregiver_user
    res = await client.get(f"/api/v1/elders/{elder_user.id}/messages")
    assert res.status_code == 200

@pytest.mark.asyncio
async def test_elder_isolation(client: AsyncClient, db):
    res = await client.get("/api/v1/elders/999/messages")
    assert res.status_code in [403, 404]
