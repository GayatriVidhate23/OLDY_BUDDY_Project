import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

@pytest.mark.asyncio
async def test_voice_simulator_websocket(db):
    # Override get_db to use the test db
    async def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    
    client = TestClient(app)
    
    from app.models import User, UserRole
    # Add dummy user for foreign key constraints
    await db.execute(User.__table__.insert().values(id=1, email="testelder@oldybuddy.internal", hashed_password="pw", role=UserRole.ELDER))
    await db.commit()
    
    with client.websocket_connect("/api/v1/voice/ws?elder_id=1") as websocket:
        # AI Greeting
        data = websocket.receive_json()
        assert data["event"] == "say"
        assert "Oldy Buddy" in data["text"]
        
        # User speaks
        websocket.send_json({"event": "speech_recognized", "text": "I need help"})
        
        # AI Response
        data = websocket.receive_json()
        assert data["event"] == "say"
        assert "Emergency alert triggered" in data["text"]
        
    app.dependency_overrides.clear()
