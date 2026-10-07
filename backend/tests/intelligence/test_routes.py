"""Unit and integration tests for intelligence conversation routes."""

import base64
import io
import logging
from unittest.mock import AsyncMock, patch
import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient

from app.core.contracts import Intent
from app.intelligence.conversation_service import get_conversation_service, reset_conversation_service
from app.intelligence.fake import FakeLLM, FakeSTT, FakeTTS, DUMMY_WAV_BYTES
from app.intelligence.factory import ProviderBundle
from app.intelligence.routes import (
    router as intelligence_router,
    get_current_user,
    get_db,
    CurrentUserStub,
    UserRole,
    MAX_AUDIO_SIZE_BYTES,
)


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Reset shared conversation service and use Fake providers for every test."""
    reset_conversation_service()
    yield
    reset_conversation_service()


@pytest.fixture
def app() -> FastAPI:
    """Create test FastAPI application with intelligence router mounted."""
    test_app = FastAPI()
    test_app.include_router(intelligence_router, prefix="/api")
    return test_app


@pytest.fixture
def elder_user() -> CurrentUserStub:
    """Mock authenticated elder user."""
    return CurrentUserStub(id=101, role=UserRole.ELDER)


@pytest.fixture
def elder_user_2() -> CurrentUserStub:
    """Mock second authenticated elder user for session isolation testing."""
    return CurrentUserStub(id=102, role=UserRole.ELDER)


@pytest.fixture
def caregiver_user() -> CurrentUserStub:
    """Mock caregiver user."""
    return CurrentUserStub(id=201, role=UserRole.CAREGIVER)


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    """Create async test client for test app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client


# ==============================================================================
# 1. AUTHENTICATION & ROLE AUTHORIZATION TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_unauthenticated_request_returns_401(client: AsyncClient) -> None:
    """Verify missing auth credentials returns HTTP 401."""
    res = await client.post(
        "/api/intelligence/converse",
        json={"text": "Hello", "session_id": "s1", "channel": "app"},
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_non_elder_role_returns_403(
    app: FastAPI, client: AsyncClient, caregiver_user: CurrentUserStub
) -> None:
    """Verify non-elder users (caregiver/admin) receive HTTP 403."""
    app.dependency_overrides[get_current_user] = lambda: caregiver_user

    res = await client.post(
        "/api/intelligence/converse",
        json={"text": "Hello", "session_id": "s1", "channel": "app"},
        headers={"Authorization": "Bearer mock_token"},
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN
    assert "Only elders may access conversation endpoints" in res.json()["detail"]


# ==============================================================================
# 2. VALIDATION TESTS (TEXT, SESSION_ID, CHANNEL, OVER-LONG)
# ==============================================================================

@pytest.mark.asyncio
async def test_empty_or_whitespace_text_returns_422(
    app: FastAPI, client: AsyncClient, elder_user: CurrentUserStub
) -> None:
    """Verify empty or whitespace-only text returns HTTP 422."""
    app.dependency_overrides[get_current_user] = lambda: elder_user

    for bad_text in ["", "   ", "\t\n  "]:
        res = await client.post(
            "/api/intelligence/converse",
            json={"text": bad_text, "session_id": "s1"},
            headers={"Authorization": "Bearer mock_token"},
        )
        assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_over_long_text_returns_422(
    app: FastAPI, client: AsyncClient, elder_user: CurrentUserStub
) -> None:
    """Verify text exceeding 1000 characters returns HTTP 422."""
    app.dependency_overrides[get_current_user] = lambda: elder_user

    long_text = "a" * 1001
    res = await client.post(
        "/api/intelligence/converse",
        json={"text": long_text, "session_id": "s1"},
        headers={"Authorization": "Bearer mock_token"},
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_invalid_session_id_returns_422(
    app: FastAPI, client: AsyncClient, elder_user: CurrentUserStub
) -> None:
    """Verify session_id containing illegal characters returns HTTP 422."""
    app.dependency_overrides[get_current_user] = lambda: elder_user

    for bad_session in ["session with space", "s!@#$", "s" * 65]:
        res = await client.post(
            "/api/intelligence/converse",
            json={"text": "Hello", "session_id": bad_session},
            headers={"Authorization": "Bearer mock_token"},
        )
        assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ==============================================================================
# 3. CONVERSE TEXT ENDPOINT SUCCESS & SESSION ISOLATION
# ==============================================================================

@pytest.mark.asyncio
async def test_elder_converse_text_success(
    app: FastAPI, client: AsyncClient, elder_user: CurrentUserStub
) -> None:
    """Verify valid text turn returns 200 with structured ConverseResponse."""
    app.dependency_overrides[get_current_user] = lambda: elder_user

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
            headers={"Authorization": "Bearer mock_token"},
        )

        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["intent"] == "talk"
        assert data["reply_text"] == "Hello! How can I help you today?"
        assert data["confidence"] == 0.98
        assert data["session_id"] == "sess-1"
        assert data["is_safe"] is True
        assert data["reply_audio_base64"] is not None


@pytest.mark.asyncio
async def test_session_isolation_between_two_elders(
    app: FastAPI, client: AsyncClient, elder_user: CurrentUserStub, elder_user_2: CurrentUserStub
) -> None:
    """Verify two elders using the same session_id maintain completely isolated histories."""
    service = get_conversation_service()

    # Elder 1 turn
    app.dependency_overrides[get_current_user] = lambda: elder_user
    await client.post(
        "/api/intelligence/converse",
        json={"text": "I am Elder 1", "session_id": "shared-session-name"},
        headers={"Authorization": "Bearer mock_token"},
    )

    # Elder 2 turn
    app.dependency_overrides[get_current_user] = lambda: elder_user_2
    await client.post(
        "/api/intelligence/converse",
        json={"text": "I am Elder 2", "session_id": "shared-session-name"},
        headers={"Authorization": "Bearer mock_token"},
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
async def test_emergency_text_calls_hook_once(
    app: FastAPI, client: AsyncClient, elder_user: CurrentUserStub
) -> None:
    """Verify emergency intent calls on_emergency_intent hook exactly once."""
    app.dependency_overrides[get_current_user] = lambda: elder_user

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
                headers={"Authorization": "Bearer mock_token"},
            )

            assert res.status_code == status.HTTP_200_OK
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
async def test_tts_failure_still_returns_200(
    app: FastAPI, client: AsyncClient, elder_user: CurrentUserStub
) -> None:
    """Verify TTS synthesis failure still returns HTTP 200 with reply_audio_base64=None."""
    app.dependency_overrides[get_current_user] = lambda: elder_user
    broken_tts = FakeTTS(error_to_raise=RuntimeError("TTS Service Unreachable"))

    with patch("app.intelligence.routes.get_providers") as mock_providers:
        mock_providers.return_value = ProviderBundle(stt=FakeSTT(), llm=FakeLLM(), tts=broken_tts)

        res = await client.post(
            "/api/intelligence/converse",
            json={"text": "Good morning", "session_id": "tts-fail-sess", "synthesize_voice": True},
            headers={"Authorization": "Bearer mock_token"},
        )

        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert len(data["reply_text"]) > 0
        assert data["reply_audio_base64"] is None


# ==============================================================================
# 5. CONVERSE AUDIO ENDPOINT TESTS (STT, SIZE, MIME TYPE)
# ==============================================================================

@pytest.mark.asyncio
async def test_converse_audio_valid_upload(
    app: FastAPI, client: AsyncClient, elder_user: CurrentUserStub
) -> None:
    """Verify audio upload transcribes, processes turn, and returns ConverseResponse."""
    app.dependency_overrides[get_current_user] = lambda: elder_user

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
            headers={"Authorization": "Bearer mock_token"},
        )

        assert res.status_code == status.HTTP_200_OK
        resp_data = res.json()
        assert resp_data["intent"] == "reminder_done"
        assert resp_data["user_transcript"] == "I took my medicine on time."
        assert resp_data["reply_text"] == "Great job taking your medicine!"
        assert resp_data["reply_audio_base64"] is not None


@pytest.mark.asyncio
async def test_converse_audio_stt_failure_returns_503_without_details(
    app: FastAPI, client: AsyncClient, elder_user: CurrentUserStub
) -> None:
    """Verify STT provider failure returns 503 with generic message (no leaked details)."""
    app.dependency_overrides[get_current_user] = lambda: elder_user
    broken_stt = FakeSTT(error_to_raise=RuntimeError("Internal Secret API Key Exhausted"))

    with patch("app.intelligence.routes.get_providers") as mock_providers:
        mock_providers.return_value = ProviderBundle(stt=broken_stt, llm=FakeLLM(), tts=FakeTTS())

        files = {"audio": ("sample.wav", io.BytesIO(DUMMY_WAV_BYTES), "audio/wav")}
        data = {"session_id": "stt-fail-sess", "channel": "app"}

        res = await client.post(
            "/api/intelligence/converse-audio",
            files=files,
            data=data,
            headers={"Authorization": "Bearer mock_token"},
        )

        assert res.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        detail = res.json()["detail"]
        assert "Internal Secret" not in detail
        assert "Voice service is currently unavailable" in detail


@pytest.mark.asyncio
async def test_converse_audio_oversized_returns_413(
    app: FastAPI, client: AsyncClient, elder_user: CurrentUserStub
) -> None:
    """Verify audio file exceeding 10MB returns HTTP 413."""
    app.dependency_overrides[get_current_user] = lambda: elder_user
    oversized_bytes = b"0" * (MAX_AUDIO_SIZE_BYTES + 100)

    files = {"audio": ("large.wav", io.BytesIO(oversized_bytes), "audio/wav")}
    data = {"session_id": "large-audio-sess", "channel": "app"}

    res = await client.post(
        "/api/intelligence/converse-audio",
        files=files,
        data=data,
        headers={"Authorization": "Bearer mock_token"},
    )

    assert res.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    assert "exceeds 10MB size limit" in res.json()["detail"]


@pytest.mark.asyncio
async def test_converse_audio_unsupported_media_type_returns_415(
    app: FastAPI, client: AsyncClient, elder_user: CurrentUserStub
) -> None:
    """Verify disallowed MIME types return HTTP 415."""
    app.dependency_overrides[get_current_user] = lambda: elder_user
    files = {"audio": ("data.txt", io.BytesIO(b"not audio"), "text/plain")}
    data = {"session_id": "bad-mime-sess", "channel": "app"}

    res = await client.post(
        "/api/intelligence/converse-audio",
        files=files,
        data=data,
        headers={"Authorization": "Bearer mock_token"},
    )

    assert res.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    assert "Unsupported audio media type" in res.json()["detail"]


# ==============================================================================
# 6. PRIVACY / LOGGING TEST
# ==============================================================================

@pytest.mark.asyncio
async def test_caplog_shows_no_user_text_or_reply(
    app: FastAPI, client: AsyncClient, elder_user: CurrentUserStub, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify user text and AI replies are NEVER logged at any log level."""
    app.dependency_overrides[get_current_user] = lambda: elder_user
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
                headers={"Authorization": "Bearer mock_token"},
            )

        assert res.status_code == status.HTTP_200_OK
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
