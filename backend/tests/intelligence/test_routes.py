"""Unit and integration tests for intelligence conversation routes."""

import base64
import io
import logging
from unittest.mock import AsyncMock, patch
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, get_password_hash
from app.core.contracts import Intent
from app.main import app
from app.models import ElderProfile, User, UserRole
from app.intelligence.conversation_service import get_conversation_service, reset_conversation_service
from app.intelligence.fake import FakeLLM, FakeSTT, FakeTTS, DUMMY_WAV_BYTES
from app.intelligence.factory import ProviderBundle
from app.intelligence.routes import router as intelligence_router, MAX_AUDIO_SIZE_BYTES

# Mount intelligence router for testing if not already registered
if not any(hasattr(r, "path") and r.path.startswith("/api/intelligence") for r in app.routes):
    app.include_router(intelligence_router, prefix="/api")


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Reset shared conversation service and use Fake providers for every test."""
    reset_conversation_service()
    yield
    reset_conversation_service()


@pytest.fixture
async def elder_user(db: AsyncSession) -> User:
    """Create a verified elder user with unique email."""
    uid = uuid.uuid4().hex[:8]
    user = User(
        email=f"elder_{uid}@example.com",
        hashed_password=get_password_hash("StrongPass123!"),
        full_name="Elder User",
        role=UserRole.ELDER,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    profile = ElderProfile(
        user_id=user.id,
        preferences={"preferred_language": "en-IN"},
    )
    db.add(profile)
    await db.commit()
    return user


@pytest.fixture
async def elder_user_2(db: AsyncSession) -> User:
    """Create a second verified elder user for session isolation testing."""
    uid = uuid.uuid4().hex[:8]
    user = User(
        email=f"elder2_{uid}@example.com",
        hashed_password=get_password_hash("StrongPass123!"),
        full_name="Second Elder",
        role=UserRole.ELDER,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def caregiver_user(db: AsyncSession) -> User:
    """Create a caregiver user with unique email."""
    uid = uuid.uuid4().hex[:8]
    user = User(
        email=f"caregiver_{uid}@example.com",
        hashed_password=get_password_hash("StrongPass123!"),
        full_name="Caregiver User",
        role=UserRole.CAREGIVER,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ==============================================================================
# 1. AUTHENTICATION & ROLE AUTHORIZATION TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_unauthenticated_request_returns_401(client: AsyncClient) -> None:
    """Verify missing auth token returns HTTP 401."""
    res = await client.post(
        "/api/intelligence/converse",
        json={"text": "Hello", "session_id": "s1", "channel": "app"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_non_elder_role_returns_403(client: AsyncClient, caregiver_user: User) -> None:
    """Verify non-elder users (caregiver/admin) receive HTTP 403."""
    token = create_access_token(caregiver_user.id)
    res = await client.post(
        "/api/intelligence/converse",
        json={"text": "Hello", "session_id": "s1", "channel": "app"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert "Only elders may access conversation endpoints" in res.json()["detail"]


# ==============================================================================
# 2. VALIDATION TESTS (TEXT, SESSION_ID, CHANNEL, OVER-LONG)
# ==============================================================================

@pytest.mark.asyncio
async def test_empty_or_whitespace_text_returns_422(client: AsyncClient, elder_user: User) -> None:
    """Verify empty or whitespace-only text returns HTTP 422."""
    token = create_access_token(elder_user.id)
    for bad_text in ["", "   ", "\t\n  "]:
        res = await client.post(
            "/api/intelligence/converse",
            json={"text": bad_text, "session_id": "s1"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_over_long_text_returns_422(client: AsyncClient, elder_user: User) -> None:
    """Verify text exceeding 1000 characters returns HTTP 422."""
    token = create_access_token(elder_user.id)
    long_text = "a" * 1001
    res = await client.post(
        "/api/intelligence/converse",
        json={"text": long_text, "session_id": "s1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_invalid_session_id_returns_422(client: AsyncClient, elder_user: User) -> None:
    """Verify session_id containing illegal characters returns HTTP 422."""
    token = create_access_token(elder_user.id)
    for bad_session in ["session with space", "s!@#$", "s" * 65]:
        res = await client.post(
            "/api/intelligence/converse",
            json={"text": "Hello", "session_id": bad_session},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 422


# ==============================================================================
# 3. CONVERSE TEXT ENDPOINT SUCCESS & SESSION ISOLATION
# ==============================================================================

@pytest.mark.asyncio
async def test_elder_converse_text_success(client: AsyncClient, elder_user: User) -> None:
    """Verify valid text turn returns 200 with structured ConverseResponse."""
    token = create_access_token(elder_user.id)
    fake_llm = FakeLLM(
        default_response='{"intent": "talk", "reply": "Hello! How can I help you today?", "confidence": 0.98}'
    )

    with patch("app.intelligence.routes.get_providers") as mock_providers:
        mock_providers.return_value = ProviderBundle(stt=FakeSTT(), llm=fake_llm, tts=FakeTTS())
        service = get_conversation_service()
        service.classifier.llm = fake_llm

        res = await client.post(
            "/api/intelligence/converse",
            json={"text": "Good morning Oldy Buddy", "session_id": "sess-1", "synthesize_voice": True},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert res.status_code == 200
        data = res.json()
        assert data["intent"] == "talk"
        assert data["reply_text"] == "Hello! How can I help you today?"
        assert data["confidence"] == 0.98
        assert data["session_id"] == "sess-1"
        assert data["is_safe"] is True
        assert data["reply_audio_base64"] is not None


@pytest.mark.asyncio
async def test_session_isolation_between_two_elders(
    client: AsyncClient, elder_user: User, elder_user_2: User
) -> None:
    """Verify two elders using the same session_id maintain completely isolated histories."""
    token1 = create_access_token(elder_user.id)
    token2 = create_access_token(elder_user_2.id)

    service = get_conversation_service()

    # Elder 1 turn
    await client.post(
        "/api/intelligence/converse",
        json={"text": "I am Elder 1", "session_id": "shared-session-name"},
        headers={"Authorization": f"Bearer {token1}"},
    )

    # Elder 2 turn
    await client.post(
        "/api/intelligence/converse",
        json={"text": "I am Elder 2", "session_id": "shared-session-name"},
        headers={"Authorization": f"Bearer {token2}"},
    )

    h1 = service.memory.get_history(elder_user.id, "shared-session-name")
    h2 = service.memory.get_history(elder_user_2.id, "shared-session-name")

    assert len(h1) == 2
    assert len(h2) == 2
    assert h1[0]["content"] == "I am Elder 1"
    assert h2[0]["content"] == "I am Elder 2"


# ==============================================================================
# 4. EMERGENCY HOOK & TTS RESILIENCE TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_emergency_text_calls_hook_once(client: AsyncClient, elder_user: User) -> None:
    """Verify emergency intent calls on_emergency_intent hook exactly once."""
    token = create_access_token(elder_user.id)
    fake_llm = FakeLLM(
        default_response='{"intent": "talk", "reply": "Tell me what is happening.", "confidence": 0.9}'
    )

    with patch("app.intelligence.routes.on_emergency_intent", new_callable=AsyncMock) as mock_hook:
        with patch("app.intelligence.routes.get_providers") as mock_providers:
            mock_providers.return_value = ProviderBundle(stt=FakeSTT(), llm=fake_llm, tts=FakeTTS())
            service = get_conversation_service()
            service.classifier.llm = fake_llm

            res = await client.post(
                "/api/intelligence/converse",
                json={"text": "I fell down in the kitchen!", "session_id": "sos-sess"},
                headers={"Authorization": f"Bearer {token}"},
            )

            assert res.status_code == 200
            data = res.json()
            assert data["intent"] == "help"
            assert data["emergency_keyword_triggered"] is True

            # Hook called once with appropriate parameters
            assert mock_hook.call_count == 1
            mock_hook.assert_called_once_with(
                elder_id=elder_user.id,
                intent=Intent.HELP,
                session_id="sos-sess",
                keyword_triggered=True,
            )


@pytest.mark.asyncio
async def test_tts_failure_still_returns_200(client: AsyncClient, elder_user: User) -> None:
    """Verify TTS synthesis failure still returns HTTP 200 with reply_audio_base64=None."""
    token = create_access_token(elder_user.id)
    broken_tts = FakeTTS(error_to_raise=RuntimeError("TTS Service Unreachable"))

    with patch("app.intelligence.routes.get_providers") as mock_providers:
        mock_providers.return_value = ProviderBundle(stt=FakeSTT(), llm=FakeLLM(), tts=broken_tts)

        res = await client.post(
            "/api/intelligence/converse",
            json={"text": "Good morning", "session_id": "tts-fail-sess", "synthesize_voice": True},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert res.status_code == 200
        data = res.json()
        assert len(data["reply_text"]) > 0
        assert data["reply_audio_base64"] is None


# ==============================================================================
# 5. CONVERSE AUDIO ENDPOINT TESTS (STT, SIZE, MIME TYPE)
# ==============================================================================

@pytest.mark.asyncio
async def test_converse_audio_valid_upload(client: AsyncClient, elder_user: User) -> None:
    """Verify audio upload transcribes, processes turn, and returns ConverseResponse."""
    token = create_access_token(elder_user.id)
    fake_stt = FakeSTT(default_transcript="I took my medicine on time.")
    fake_llm = FakeLLM(
        default_response='{"intent": "reminder_done", "reply": "Great job taking your medicine!", "confidence": 0.99}'
    )

    with patch("app.intelligence.routes.get_providers") as mock_providers:
        mock_providers.return_value = ProviderBundle(stt=fake_stt, llm=fake_llm, tts=FakeTTS())
        service = get_conversation_service()
        service.classifier.llm = fake_llm

        files = {"audio": ("sample.wav", io.BytesIO(DUMMY_WAV_BYTES), "audio/wav")}
        data = {"session_id": "audio-sess-1", "channel": "app", "synthesize_voice": "true"}

        res = await client.post(
            "/api/intelligence/converse-audio",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert res.status_code == 200
        resp_data = res.json()
        assert resp_data["intent"] == "reminder_done"
        assert resp_data["user_transcript"] == "I took my medicine on time."
        assert resp_data["reply_text"] == "Great job taking your medicine!"
        assert resp_data["reply_audio_base64"] is not None


@pytest.mark.asyncio
async def test_converse_audio_stt_failure_returns_503_without_details(
    client: AsyncClient, elder_user: User
) -> None:
    """Verify STT provider failure returns 503 with generic message (no leaked details)."""
    token = create_access_token(elder_user.id)
    broken_stt = FakeSTT(error_to_raise=RuntimeError("Internal Secret API Key Exhausted"))

    with patch("app.intelligence.routes.get_providers") as mock_providers:
        mock_providers.return_value = ProviderBundle(stt=broken_stt, llm=FakeLLM(), tts=FakeTTS())

        files = {"audio": ("sample.wav", io.BytesIO(DUMMY_WAV_BYTES), "audio/wav")}
        data = {"session_id": "stt-fail-sess", "channel": "app"}

        res = await client.post(
            "/api/intelligence/converse-audio",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert res.status_code == 503
        detail = res.json()["detail"]
        assert "Internal Secret" not in detail
        assert "Voice service is currently unavailable" in detail


@pytest.mark.asyncio
async def test_converse_audio_oversized_returns_413(client: AsyncClient, elder_user: User) -> None:
    """Verify audio file exceeding 10MB returns HTTP 413."""
    token = create_access_token(elder_user.id)
    oversized_bytes = b"0" * (MAX_AUDIO_SIZE_BYTES + 100)

    files = {"audio": ("large.wav", io.BytesIO(oversized_bytes), "audio/wav")}
    data = {"session_id": "large-audio-sess", "channel": "app"}

    res = await client.post(
        "/api/intelligence/converse-audio",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 413
    assert "exceeds 10MB size limit" in res.json()["detail"]


@pytest.mark.asyncio
async def test_converse_audio_unsupported_media_type_returns_415(
    client: AsyncClient, elder_user: User
) -> None:
    """Verify disallowed MIME types return HTTP 415."""
    token = create_access_token(elder_user.id)
    files = {"audio": ("data.txt", io.BytesIO(b"not audio"), "text/plain")}
    data = {"session_id": "bad-mime-sess", "channel": "app"}

    res = await client.post(
        "/api/intelligence/converse-audio",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 415
    assert "Unsupported audio media type" in res.json()["detail"]


# ==============================================================================
# 6. PRIVACY / LOGGING TEST
# ==============================================================================

@pytest.mark.asyncio
async def test_caplog_shows_no_user_text_or_reply(
    client: AsyncClient, elder_user: User, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify user text and AI replies are NEVER logged at any log level."""
    token = create_access_token(elder_user.id)
    private_user_text = "SECRET_USER_MEDICAL_HISTORY_PRIVATE_12345"
    private_reply = "SECRET_AI_REPLY_DIAGNOSTIC_PRIVATE_67890"

    fake_llm = FakeLLM(
        default_response=f'{{"intent": "talk", "reply": "{private_reply}", "confidence": 0.95}}'
    )

    with patch("app.intelligence.routes.get_providers") as mock_providers:
        mock_providers.return_value = ProviderBundle(stt=FakeSTT(), llm=fake_llm, tts=FakeTTS())
        service = get_conversation_service()
        service.classifier.llm = fake_llm

        with caplog.at_level(logging.DEBUG):
            res = await client.post(
                "/api/intelligence/converse",
                json={"text": private_user_text, "session_id": "privacy-sess"},
                headers={"Authorization": f"Bearer {token}"},
            )

        assert res.status_code == 200
        # Assert neither user private text nor private reply appear in any log record
        for record in caplog.records:
            assert private_user_text not in record.message
            assert private_reply not in record.message


# ==============================================================================
# 7. SINGLETON FACTORY TEST
# ==============================================================================

def test_shared_conversation_service_singleton() -> None:
    """Verify get_conversation_service returns the same shared instance across calls."""
    reset_conversation_service()
    service1 = get_conversation_service()
    service2 = get_conversation_service()
    assert service1 is service2
