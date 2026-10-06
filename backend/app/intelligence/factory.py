"""Factory to obtain configured STT, LLM, and TTS providers."""

from dataclasses import dataclass
import os
from typing import Optional

from app.intelligence.base import STTProvider, LLMProvider, TTSProvider
from app.intelligence.fake import FakeSTT, FakeLLM, FakeTTS
from app.intelligence.sarvam import SarvamSTT, SarvamLLM, SarvamTTS
from app.intelligence.exceptions import ProviderError


@dataclass(frozen=True)
class ProviderBundle:
    """Container for the full intelligence provider pipeline."""

    stt: STTProvider
    llm: LLMProvider
    tts: TTSProvider


def get_providers(
    provider_type: Optional[str] = None,
    api_key: Optional[str] = None,
) -> ProviderBundle:
    """Obtain the configured STT, LLM, and TTS providers.

    Args:
        provider_type: Explicit provider selector ('sarvam' or 'fake'). If None,
            reads from SARVAM_PROVIDER or INTELLIGENCE_PROVIDER env var, or falls back to 'fake'.
        api_key: Optional API key for external providers. If None, reads from SARVAM_API_KEY.

    Returns:
        ProviderBundle containing (stt, llm, tts) provider instances.
    """
    selected_type = (
        provider_type
        or os.environ.get("INTELLIGENCE_PROVIDER")
        or os.environ.get("SARVAM_PROVIDER")
        or "fake"
    ).lower().strip()

    if selected_type == "sarvam":
        resolved_key = api_key or os.environ.get("SARVAM_API_KEY")
        if not resolved_key:
            raise ProviderError("SARVAM_API_KEY environment variable or argument is required", provider_name="get_providers")
        return ProviderBundle(
            stt=SarvamSTT(api_key=resolved_key),
            llm=SarvamLLM(api_key=resolved_key),
            tts=SarvamTTS(api_key=resolved_key),
        )

    # Default to fake providers for testing and local development
    return ProviderBundle(
        stt=FakeSTT(),
        llm=FakeLLM(),
        tts=FakeTTS(),
    )
