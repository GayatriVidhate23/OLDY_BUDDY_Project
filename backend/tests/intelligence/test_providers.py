"""Unit tests for Intelligence Layer provider adapters (Fake & Sarvam interfaces)."""

import pytest
from app.core.contracts import Intent, EventType
from app.intelligence.base import STTProvider, LLMProvider, TTSProvider
from app.intelligence.exceptions import ProviderError
from app.intelligence.fake import FakeSTT, FakeLLM, FakeTTS, DUMMY_WAV_BYTES
from app.intelligence.sarvam import SarvamSTT, SarvamLLM, SarvamTTS
from app.intelligence.factory import get_providers, ProviderBundle


def test_contracts_intent_enum() -> None:
    """Verify all required Intent enum values exist with exact string names."""
    expected_intents = {
        "talk",
        "help",
        "reminder_done",
        "reminder_forgot",
        "food",
        "sos",
        "unknown",
    }
    actual_intents = {intent.value for intent in Intent}
    assert actual_intents == expected_intents


def test_contracts_event_type_enum() -> None:
    """Verify all required EventType enum values exist with exact string names."""
    expected_events = {
        "checkin_ok",
        "checkin_concern",
        "checkin_missed",
        "reminder_done",
        "reminder_missed",
        "help_request",
        "sos",
    }
    actual_events = {event.value for event in EventType}
    assert actual_events == expected_events


@pytest.mark.asyncio
async def test_fake_stt_transcription() -> None:
    """Verify FakeSTT transcription and call recording."""
    stt = FakeSTT(default_transcript="I took my medicine on time.")
    assert isinstance(stt, STTProvider)

    audio = b"dummy_audio_bytes"
    result = await stt.transcribe(audio, language="hi-IN")

    assert result == "I took my medicine on time."
    assert len(stt.calls) == 1
    assert stt.calls[0]["audio_bytes"] == audio
    assert stt.calls[0]["language"] == "hi-IN"


@pytest.mark.asyncio
async def test_fake_stt_empty_audio_raises_error() -> None:
    """Verify FakeSTT raises ProviderError when audio_bytes is empty."""
    stt = FakeSTT()
    with pytest.raises(ProviderError) as exc_info:
        await stt.transcribe(b"")
    assert "Cannot transcribe empty audio" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fake_stt_error_to_raise() -> None:
    """Verify FakeSTT raises custom configured errors."""
    stt = FakeSTT(error_to_raise=ProviderError("Simulated STT failure", provider_name="FakeSTT"))
    with pytest.raises(ProviderError) as exc_info:
        await stt.transcribe(b"audio")
    assert "Simulated STT failure" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fake_llm_completion() -> None:
    """Verify FakeLLM completion and call recording."""
    llm = FakeLLM(default_response='{"intent": "talk", "reply": "Hello! How are you feeling?"}')
    assert isinstance(llm, LLMProvider)

    messages = [{"role": "user", "content": "Good morning"}]
    response = await llm.complete(messages, temperature=0.7)

    assert response == '{"intent": "talk", "reply": "Hello! How are you feeling?"}'
    assert len(llm.calls) == 1
    assert llm.calls[0]["messages"] == messages
    assert llm.calls[0]["opts"] == {"temperature": 0.7}


@pytest.mark.asyncio
async def test_fake_llm_custom_handler() -> None:
    """Verify FakeLLM supports custom handler function."""
    def handler(messages: list[dict[str, str]], opts: dict) -> str:
        return f"Echo: {messages[-1]['content']}"

    llm = FakeLLM(custom_handler=handler)
    messages = [{"role": "user", "content": "I need help with my tea."}]
    response = await llm.complete(messages)
    assert response == "Echo: I need help with my tea."


@pytest.mark.asyncio
async def test_fake_llm_empty_messages_raises_error() -> None:
    """Verify FakeLLM raises ProviderError when messages list is empty."""
    llm = FakeLLM()
    with pytest.raises(ProviderError) as exc_info:
        await llm.complete([])
    assert "Messages list cannot be empty" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fake_tts_synthesis() -> None:
    """Verify FakeTTS audio synthesis and call recording."""
    tts = FakeTTS()
    assert isinstance(tts, TTSProvider)

    audio_bytes = await tts.synthesize("Take your medicine", language="en-IN")
    assert audio_bytes == DUMMY_WAV_BYTES
    assert len(tts.calls) == 1
    assert tts.calls[0]["text"] == "Take your medicine"
    assert tts.calls[0]["language"] == "en-IN"


@pytest.mark.asyncio
async def test_fake_tts_empty_text_raises_error() -> None:
    """Verify FakeTTS raises ProviderError on empty or whitespace text."""
    tts = FakeTTS()
    with pytest.raises(ProviderError) as exc_info:
        await tts.synthesize("   ")
    assert "Cannot synthesize empty text" in str(exc_info.value)


def test_sarvam_providers_init_validation() -> None:
    """Verify Sarvam provider classes validate missing API keys upon creation."""
    with pytest.raises(ProviderError):
        SarvamSTT(api_key="")

    with pytest.raises(ProviderError):
        SarvamLLM(api_key="")

    with pytest.raises(ProviderError):
        SarvamTTS(api_key="")

    stt = SarvamSTT(api_key="test_key_123")
    llm = SarvamLLM(api_key="test_key_123")
    tts = SarvamTTS(api_key="test_key_123")

    assert isinstance(stt, STTProvider)
    assert isinstance(llm, LLMProvider)
    assert isinstance(tts, TTSProvider)


def test_get_providers_factory_fake() -> None:
    """Verify factory returns Fake providers when provider_type is 'fake' or default."""
    bundle = get_providers(provider_type="fake")
    assert isinstance(bundle, ProviderBundle)
    assert isinstance(bundle.stt, FakeSTT)
    assert isinstance(bundle.llm, FakeLLM)
    assert isinstance(bundle.tts, FakeTTS)


def test_get_providers_factory_sarvam() -> None:
    """Verify factory returns Sarvam providers when configured."""
    bundle = get_providers(provider_type="sarvam", api_key="sk_test_sarvam_key")
    assert isinstance(bundle, ProviderBundle)
    assert isinstance(bundle.stt, SarvamSTT)
    assert isinstance(bundle.llm, SarvamLLM)
    assert isinstance(bundle.tts, SarvamTTS)


def test_get_providers_factory_sarvam_missing_key_raises() -> None:
    """Verify factory raises ProviderError if Sarvam selected without API key."""
    with pytest.raises(ProviderError) as exc_info:
        get_providers(provider_type="sarvam", api_key="")
    assert "SARVAM_API_KEY" in str(exc_info.value)
