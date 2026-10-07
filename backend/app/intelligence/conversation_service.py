"""Conversation service orchestrating intent classification, memory, and safety guardrails.

Note: Short-term memory is in-memory and per-process only.
"""

import time
from typing import Any, Callable, Optional

from app.core.contracts import Intent
from app.intelligence.classifier import IntentClassifier
from app.intelligence.exceptions import ProviderError
from app.intelligence.guardrails import (
    apply_guardrails,
    check_emergency_keyword_upgrade,
    NEUTRAL_EMERGENCY_REPLY,
)
from app.intelligence.schemas import ConverseResult

# Named constants
CONFIDENCE_THRESHOLD: float = 0.60
DEFAULT_SESSION_TTL_SECONDS: float = 1800.0  # 30 minutes
DEFAULT_MAX_SESSIONS: int = 1000
DEFAULT_MAX_TURNS_PER_SESSION: int = 6  # 3 user-assistant exchange pairs

# Language constants
SUPPORTED_LANGUAGES = {"en-IN", "hi-IN", "mr-IN"}
DEFAULT_LANGUAGE = "en-IN"

# Language-aware messages
PLEASE_REPEAT_MESSAGES: dict[str, str] = {
    "en-IN": "I'm sorry, I didn't quite catch that. Could you please repeat what you said?",
    "hi-IN": "माफ़ कीजिए, मैं समझ नहीं पाया। क्या आप कृपया दोबारा बोल सकते हैं?",
    "mr-IN": "क्षमस्व, मला नीट समजले नाही. कृपया पुन्हा सांगाल का?",
}

TROUBLE_CONNECTING_MESSAGES: dict[str, str] = {
    "en-IN": "I am having a little trouble connecting right now. Please try again in a moment.",
    "hi-IN": "मुझे अभी संपर्क करने में थोड़ी परेशानी हो रही है। कृपया कुछ देर बाद फिर से प्रयास करें।",
    "mr-IN": "मला सध्या संपर्क साधण्यात थोडी अडचण येत आहे. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा.",
}

NEUTRAL_EMERGENCY_MESSAGES: dict[str, str] = {
    "en-IN": NEUTRAL_EMERGENCY_REPLY,
    "hi-IN": "क्या आप ठीक हैं? मुझे बताइए क्या हुआ।",
    "mr-IN": "तुम्ही ठीक आहात का? मला सांगा काय झाले.",
}


def normalize_language_code(raw_code: Optional[str]) -> str:
    """Normalize raw language codes to standard locale format.

    Examples: 'hi', 'hi_in', 'HI-IN' -> 'hi-IN'.
    Unsupported languages fall back to 'en-IN'.
    """
    if not raw_code:
        return DEFAULT_LANGUAGE

    clean = raw_code.strip().lower().replace("_", "-")
    if clean in ("hi", "hi-in", "hindi"):
        return "hi-IN"
    elif clean in ("mr", "mr-in", "marathi"):
        return "mr-IN"
    elif clean in ("en", "en-in", "en-us", "en-gb", "english"):
        return "en-IN"

    return DEFAULT_LANGUAGE


class ShortTermMemory:
    """In-memory sliding window cache of recent dialogue turns.

    Note: In-memory, per-process storage only.
    Keyed by (elder_id, session_id).
    """

    def __init__(
        self,
        ttl_seconds: float = DEFAULT_SESSION_TTL_SECONDS,
        max_sessions: int = DEFAULT_MAX_SESSIONS,
        max_turns: int = DEFAULT_MAX_TURNS_PER_SESSION,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions
        self.max_turns = max_turns
        self.clock = clock
        self._sessions: dict[tuple[int, str], dict[str, Any]] = {}

    def _purge_expired(self) -> None:
        """Purge sessions exceeding TTL."""
        now = self.clock()
        expired_keys = [
            key
            for key, data in self._sessions.items()
            if (now - data["last_accessed"]) > self.ttl_seconds
        ]
        for key in expired_keys:
            del self._sessions[key]

    def get_history(self, elder_id: int, session_id: str) -> list[dict[str, str]]:
        """Retrieve recent dialogue turns for this session."""
        self._purge_expired()
        key = (elder_id, session_id)
        session_data = self._sessions.get(key)
        if not session_data:
            return []

        session_data["last_accessed"] = self.clock()
        return list(session_data["turns"])

    def add_turn(self, elder_id: int, session_id: str, role: str, content: str) -> None:
        """Add a turn to the sliding window history."""
        self._purge_expired()
        key = (elder_id, session_id)
        now = self.clock()

        if key not in self._sessions:
            if len(self._sessions) >= self.max_sessions:
                # Evict oldest session
                oldest_key = min(self._sessions.keys(), key=lambda k: self._sessions[k]["last_accessed"])
                del self._sessions[oldest_key]
            self._sessions[key] = {"turns": [], "last_accessed": now}

        session_data = self._sessions[key]
        session_data["last_accessed"] = now
        session_data["turns"].append({"role": role, "content": content})

        # Apply sliding window cap
        if len(session_data["turns"]) > self.max_turns:
            session_data["turns"] = session_data["turns"][-self.max_turns :]

    def clear_session(self, elder_id: int, session_id: str) -> None:
        """Public method to clear session history upon call/session end."""
        self._purge_expired()
        key = (elder_id, session_id)
        self._sessions.pop(key, None)


class ConversationService:
    """Orchestrates multi-turn elderly conversation, classification, and safety."""

    def __init__(
        self,
        classifier: Optional[IntentClassifier] = None,
        memory: Optional[ShortTermMemory] = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.classifier = classifier or IntentClassifier()
        self.memory = memory or ShortTermMemory(clock=clock)
        self.clock = clock

    async def process_turn(
        self,
        elder_id: int,
        session_id: str,
        user_text: str,
        profile_context: Optional[dict[str, Any]] = None,
    ) -> ConverseResult:
        """Process a conversation turn and return a safe, structured reply.

        Args:
            elder_id: Unique ID of the elder.
            session_id: Conversation session identifier.
            user_text: User speech utterance.
            profile_context: Optional elder preferences/routines dictionary.

        Returns:
            ConverseResult containing intent, sanitized reply, and safety status.
        """
        # 1. Resolve & normalize language from profile context (never hardcode)
        raw_lang = (
            profile_context.get("preferred_language")
            or profile_context.get("language")
            if profile_context
            else None
        )
        language = normalize_language_code(raw_lang)

        # 2. Retrieve short-term history for (elder_id, session_id)
        history = self.memory.get_history(elder_id, session_id)

        # 3. Classify intent via LLM with error shielding
        provider_failed = False
        try:
            classif_res = await self.classifier.classify(
                user_text=user_text,
                conversation_history=history,
                context=profile_context,
            )
            raw_intent = classif_res.intent
            raw_reply = classif_res.reply
            confidence = classif_res.confidence
        except (ProviderError, Exception):
            raw_intent = Intent.UNKNOWN
            raw_reply = ""
            confidence = 0.0
            provider_failed = True

        # 4. Check deterministic emergency keyword upgrade
        final_intent = check_emergency_keyword_upgrade(user_text, current_intent=raw_intent)
        emergency_keyword_triggered = (final_intent != raw_intent and final_intent == Intent.HELP)

        # 5. Formulate candidate reply
        is_repeat_turn = False

        if final_intent in (Intent.SOS, Intent.HELP):
            # For SOS/HELP: NEVER apply "please repeat" fallback, even with low confidence or provider error
            if provider_failed or not raw_reply:
                candidate_reply = NEUTRAL_EMERGENCY_MESSAGES.get(language, NEUTRAL_EMERGENCY_REPLY)
            else:
                candidate_reply = raw_reply
        elif provider_failed:
            # Provider failure on non-emergency: language-aware "having trouble"
            candidate_reply = TROUBLE_CONNECTING_MESSAGES.get(language, TROUBLE_CONNECTING_MESSAGES[DEFAULT_LANGUAGE])
            is_repeat_turn = True
        elif final_intent == Intent.UNKNOWN or confidence < CONFIDENCE_THRESHOLD:
            # Low confidence or unknown intent: language-aware "please repeat"
            candidate_reply = PLEASE_REPEAT_MESSAGES.get(language, PLEASE_REPEAT_MESSAGES[DEFAULT_LANGUAGE])
            is_repeat_turn = True
        else:
            # Normal conversation turn
            candidate_reply = raw_reply

        # 6. Apply safety guardrails (never alters intent)
        guardrail_res = apply_guardrails(candidate_reply, intent=final_intent)
        sanitized_reply = guardrail_res.sanitized_reply

        # 7. Update short-term memory (do not store "please repeat" or transient failure turns)
        if not is_repeat_turn and user_text.strip():
            self.memory.add_turn(elder_id, session_id, role="user", content=user_text)
            self.memory.add_turn(elder_id, session_id, role="assistant", content=sanitized_reply)

        # 8. Return structured response (never log text or replies directly)
        return ConverseResult(
            elder_id=elder_id,
            session_id=session_id,
            intent=final_intent,
            reply=sanitized_reply,
            confidence=confidence,
            is_safe=guardrail_res.is_safe,
            violations=guardrail_res.violations,
            language=language,
            emergency_keyword_triggered=emergency_keyword_triggered,
        )


# Shared module-level singleton instance for in-process and route sharing
_shared_conversation_service: Optional[ConversationService] = None


def get_conversation_service(
    classifier: Optional[IntentClassifier] = None,
    memory: Optional[ShortTermMemory] = None,
) -> ConversationService:
    """Return the shared singleton ConversationService instance."""
    global _shared_conversation_service
    if _shared_conversation_service is None:
        _shared_conversation_service = ConversationService(
            classifier=classifier,
            memory=memory,
        )
    return _shared_conversation_service


def reset_conversation_service() -> None:
    """Reset the singleton instance (useful for test isolation)."""
    global _shared_conversation_service
    _shared_conversation_service = None
