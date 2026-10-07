"""Sarvam.ai provider implementations for STT, LLM, and TTS using async httpx."""

import base64
from typing import Any, Optional
import httpx

from app.intelligence.base import STTProvider, LLMProvider, TTSProvider
from app.intelligence.exceptions import ProviderError

DEFAULT_SARVAM_BASE_URL = "https://api.sarvam.ai"
DEFAULT_TIMEOUT_SECONDS = 30.0


class SarvamSTT(STTProvider):
    """Speech-to-Text provider using Sarvam.ai Saaras model."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_SARVAM_BASE_URL,
        model: str = "saaras:v4",
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if not api_key:
            raise ProviderError("API key is required for SarvamSTT", provider_name="SarvamSTT")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def transcribe(self, audio_bytes: bytes, language: str = "hi-IN") -> str:
        """Transcribe speech audio bytes into text via Sarvam STT REST API."""
        if not audio_bytes:
            raise ProviderError("Cannot transcribe empty audio bytes", provider_name="SarvamSTT")

        endpoint = f"{self.base_url}/speech-to-text"
        headers = {"api-subscription-key": self.api_key}
        files = {"file": ("input.wav", audio_bytes, "audio/wav")}
        data = {
            "model": self.model,
            "language_code": language,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(endpoint, headers=headers, files=files, data=data)

            if response.status_code != 200:
                raise ProviderError(
                    f"STT transcription failed with status {response.status_code}: {response.text}",
                    provider_name="SarvamSTT",
                    status_code=response.status_code,
                )

            payload = response.json()
            transcript = payload.get("transcript")
            if transcript is None:
                raise ProviderError("Missing 'transcript' in response payload", provider_name="SarvamSTT")

            return str(transcript)

        except httpx.HTTPError as err:
            raise ProviderError(f"HTTP network error during STT: {err}", provider_name="SarvamSTT") from err
        except Exception as err:
            if isinstance(err, ProviderError):
                raise
            raise ProviderError(f"Unexpected error during STT: {err}", provider_name="SarvamSTT") from err


class SarvamLLM(LLMProvider):
    """Large Language Model provider using Sarvam.ai Chat Completions API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_SARVAM_BASE_URL,
        model: str = "sarvam-105b-conversations",
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if not api_key:
            raise ProviderError("API key is required for SarvamLLM", provider_name="SarvamLLM")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def complete(self, messages: list[dict[str, str]], **opts: Any) -> str:
        """Generate a chat completion response using Sarvam LLM API."""
        if not messages:
            raise ProviderError("Messages list cannot be empty", provider_name="SarvamLLM")

        endpoint = f"{self.base_url}/v1/chat/completions"
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": opts.pop("model", self.model),
            "messages": messages,
            **opts,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(endpoint, headers=headers, json=payload)

            if response.status_code != 200:
                raise ProviderError(
                    f"LLM completion failed with status {response.status_code}: {response.text}",
                    provider_name="SarvamLLM",
                    status_code=response.status_code,
                )

            data = response.json()
            choices = data.get("choices")
            if not choices or not isinstance(choices, list):
                raise ProviderError("Invalid response format: 'choices' missing or empty", provider_name="SarvamLLM")

            message = choices[0].get("message", {})
            content = message.get("content")
            if content is None:
                raise ProviderError("Missing 'content' in completion choice message", provider_name="SarvamLLM")

            return str(content)

        except httpx.HTTPError as err:
            raise ProviderError(f"HTTP network error during LLM completion: {err}", provider_name="SarvamLLM") from err
        except Exception as err:
            if isinstance(err, ProviderError):
                raise
            raise ProviderError(f"Unexpected error during LLM completion: {err}", provider_name="SarvamLLM") from err


class SarvamTTS(TTSProvider):
    """Text-to-Speech provider using Sarvam.ai Bulbul model."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_SARVAM_BASE_URL,
        model: str = "bulbul:v3",
        speaker: str = "shubh",
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if not api_key:
            raise ProviderError("API key is required for SarvamTTS", provider_name="SarvamTTS")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.speaker = speaker
        self.timeout = timeout

    async def synthesize(self, text: str, language: str = "hi-IN") -> bytes:
        """Synthesize text into speech audio bytes via Sarvam TTS REST API."""
        if not text or not text.strip():
            raise ProviderError("Cannot synthesize empty text", provider_name="SarvamTTS")

        endpoint = f"{self.base_url}/text-to-speech"
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "language_code": language,
            "speaker": self.speaker,
            "model": self.model,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(endpoint, headers=headers, json=payload)

            if response.status_code != 200:
                raise ProviderError(
                    f"TTS synthesis failed with status {response.status_code}: {response.text}",
                    provider_name="SarvamTTS",
                    status_code=response.status_code,
                )

            data = response.json()
            audios = data.get("audios")
            if not audios or not isinstance(audios, list):
                raise ProviderError("Missing or empty 'audios' in TTS response", provider_name="SarvamTTS")

            audio_b64 = audios[0]
            return base64.b64decode(audio_b64)

        except httpx.HTTPError as err:
            raise ProviderError(f"HTTP network error during TTS synthesis: {err}", provider_name="SarvamTTS") from err
        except Exception as err:
            if isinstance(err, ProviderError):
                raise
            raise ProviderError(f"Unexpected error during TTS synthesis: {err}", provider_name="SarvamTTS") from err
