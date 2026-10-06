"""Deterministic fake provider implementations for testing."""

from typing import Any, Callable, Optional
from app.intelligence.base import STTProvider, LLMProvider, TTSProvider
from app.intelligence.exceptions import ProviderError

# Minimal valid 44-byte WAV header for deterministic test audio
DUMMY_WAV_BYTES = (
    b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
    b"D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
)


class FakeSTT(STTProvider):
    """Deterministic Fake Speech-to-Text provider for tests."""

    def __init__(
        self,
        default_transcript: str = "I took my morning medicine.",
        error_to_raise: Optional[Exception] = None,
    ) -> None:
        self.default_transcript = default_transcript
        self.error_to_raise = error_to_raise
        self.calls: list[dict[str, Any]] = []

    async def transcribe(self, audio_bytes: bytes, language: str = "hi-IN") -> str:
        """Return deterministic transcript and record invocation."""
        if self.error_to_raise:
            raise self.error_to_raise

        if not audio_bytes:
            raise ProviderError("Cannot transcribe empty audio bytes", provider_name="FakeSTT")

        self.calls.append({"audio_bytes": audio_bytes, "language": language})
        return self.default_transcript


class FakeLLM(LLMProvider):
    """Deterministic Fake Large Language Model provider for tests."""

    def __init__(
        self,
        default_response: str = '{"intent": "reminder_done", "reply": "Great job taking your medicine!", "confidence": 0.95}',
        error_to_raise: Optional[Exception] = None,
        custom_handler: Optional[Callable[[list[dict[str, str]], dict[str, Any]], str]] = None,
    ) -> None:
        self.default_response = default_response
        self.error_to_raise = error_to_raise
        self.custom_handler = custom_handler
        self.calls: list[dict[str, Any]] = []

    async def complete(self, messages: list[dict[str, str]], **opts: Any) -> str:
        """Return deterministic completion and record invocation."""
        if self.error_to_raise:
            raise self.error_to_raise

        if not messages:
            raise ProviderError("Messages list cannot be empty", provider_name="FakeLLM")

        self.calls.append({"messages": messages, "opts": opts})

        if self.custom_handler:
            return self.custom_handler(messages, opts)

        return self.default_response


class FakeTTS(TTSProvider):
    """Deterministic Fake Text-to-Speech provider for tests."""

    def __init__(
        self,
        default_audio: bytes = DUMMY_WAV_BYTES,
        error_to_raise: Optional[Exception] = None,
    ) -> None:
        self.default_audio = default_audio
        self.error_to_raise = error_to_raise
        self.calls: list[dict[str, Any]] = []

    async def synthesize(self, text: str, language: str = "hi-IN") -> bytes:
        """Return deterministic audio bytes and record invocation."""
        if self.error_to_raise:
            raise self.error_to_raise

        if not text or not text.strip():
            raise ProviderError("Cannot synthesize empty text", provider_name="FakeTTS")

        self.calls.append({"text": text, "language": language})
        return self.default_audio
