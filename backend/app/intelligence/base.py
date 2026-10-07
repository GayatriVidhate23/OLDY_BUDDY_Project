"""Abstract base classes for speech-to-text, LLM, and text-to-speech providers."""

from abc import ABC, abstractmethod
from typing import Any


class STTProvider(ABC):
    """Abstract interface for Speech-to-Text providers."""

    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, language: str = "hi-IN") -> str:
        """Transcribe speech audio bytes into text.

        Args:
            audio_bytes: Raw audio binary data.
            language: Language code (e.g. 'hi-IN', 'en-IN').

        Returns:
            Transcribed text.

        Raises:
            ProviderError: If transcription fails.
        """
        pass


class LLMProvider(ABC):
    """Abstract interface for Large Language Model providers."""

    @abstractmethod
    async def complete(self, messages: list[dict[str, str]], **opts: Any) -> str:
        """Generate a chat completion response from a list of messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            **opts: Additional provider-specific parameters (e.g., temperature, max_tokens).

        Returns:
            Model completion text.

        Raises:
            ProviderError: If generation fails.
        """
        pass


class TTSProvider(ABC):
    """Abstract interface for Text-to-Speech providers."""

    @abstractmethod
    async def synthesize(self, text: str, language: str = "hi-IN") -> bytes:
        """Synthesize text into speech audio bytes.

        Args:
            text: Text to synthesize into speech.
            language: Target language code (e.g. 'hi-IN', 'en-IN').

        Returns:
            Synthesized audio bytes (e.g. WAV format).

        Raises:
            ProviderError: If synthesis fails.
        """
        pass
