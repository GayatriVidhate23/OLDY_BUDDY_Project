"""Oldy Buddy Intelligence Layer - Speech, LLM, and Audio processing."""

from app.intelligence.base import STTProvider, LLMProvider, TTSProvider
from app.intelligence.exceptions import ProviderError
from app.intelligence.fake import FakeSTT, FakeLLM, FakeTTS, DUMMY_WAV_BYTES
from app.intelligence.sarvam import SarvamSTT, SarvamLLM, SarvamTTS
from app.intelligence.factory import get_providers, ProviderBundle
from app.intelligence.schemas import IntentClassificationResult, GuardrailResult
from app.intelligence.classifier import IntentClassifier
from app.intelligence.guardrails import (
    apply_guardrails,
    check_emergency_keyword_upgrade,
    normalize_text,
    NEUTRAL_EMERGENCY_REPLY,
    MEDICAL_SAFETY_FALLBACK,
    STRONG_EMERGENCY_PATTERNS,
    WEAK_EMERGENCY_PATTERNS,
)

__all__ = [
    "STTProvider",
    "LLMProvider",
    "TTSProvider",
    "ProviderError",
    "FakeSTT",
    "FakeLLM",
    "FakeTTS",
    "DUMMY_WAV_BYTES",
    "SarvamSTT",
    "SarvamLLM",
    "SarvamTTS",
    "get_providers",
    "ProviderBundle",
    "IntentClassificationResult",
    "GuardrailResult",
    "IntentClassifier",
    "apply_guardrails",
    "check_emergency_keyword_upgrade",
    "normalize_text",
    "NEUTRAL_EMERGENCY_REPLY",
    "MEDICAL_SAFETY_FALLBACK",
    "STRONG_EMERGENCY_PATTERNS",
    "WEAK_EMERGENCY_PATTERNS",
]
