"""Unit tests for ConversationService and ShortTermMemory."""

import pytest
from app.core.contracts import Intent
from app.intelligence.classifier import IntentClassifier
from app.intelligence.conversation_service import (
    ConversationService,
    ShortTermMemory,
    normalize_language_code,
    CONFIDENCE_THRESHOLD,
    PLEASE_REPEAT_MESSAGES,
    TROUBLE_CONNECTING_MESSAGES,
)
from app.intelligence.exceptions import ProviderError
from app.intelligence.fake import FakeLLM
from app.intelligence.schemas import ConverseResult


# ==============================================================================
# 1. LANGUAGE NORMALIZATION TESTS
# ==============================================================================

@pytest.mark.parametrize(
    "input_lang, expected_normalized",
    [
        ("hi", "hi-IN"),
        ("hi_in", "hi-IN"),
        ("HI-IN", "hi-IN"),
        ("hindi", "hi-IN"),
        ("mr", "mr-IN"),
        ("mr_IN", "mr-IN"),
        ("marathi", "mr-IN"),
        ("en", "en-IN"),
        ("en_US", "en-IN"),
        ("en-GB", "en-IN"),
        ("english", "en-IN"),
        ("french", "en-IN"),  # Unsupported falls back to English
        ("de_DE", "en-IN"),   # Unsupported falls back to English
        (None, "en-IN"),
        ("", "en-IN"),
    ],
)
def test_normalize_language_code(input_lang: str | None, expected_normalized: str) -> None:
    """Verify language code normalization and fallback for unsupported languages."""
    assert normalize_language_code(input_lang) == expected_normalized


# ==============================================================================
# 2. SHORT-TERM MEMORY TESTS (CLOCK, TTL, SLIDING WINDOW, SESSION CAP)
# ==============================================================================

def test_memory_ttl_with_fake_clock() -> None:
    """Verify that sessions exceeding TTL are purged using an injected clock."""
    current_time = 1000.0

    def fake_clock() -> float:
        return current_time

    memory = ShortTermMemory(ttl_seconds=300.0, clock=fake_clock)

    memory.add_turn(elder_id=1, session_id="call-123", role="user", content="Hello")
    memory.add_turn(elder_id=1, session_id="call-123", role="assistant", content="Hi there")

    # Access within TTL
    current_time = 1100.0
    history = memory.get_history(elder_id=1, session_id="call-123")
    assert len(history) == 2

    # Advance clock past TTL (300s)
    current_time = 1450.0  # 350s since last access
    expired_history = memory.get_history(elder_id=1, session_id="call-123")
    assert expired_history == []


def test_memory_sliding_window_limit() -> None:
    """Verify sliding window cap retains only the most recent N turns."""
    memory = ShortTermMemory(max_turns=4)

    for i in range(1, 7):
        memory.add_turn(elder_id=1, session_id="s1", role="user", content=f"Message {i}")

    history = memory.get_history(elder_id=1, session_id="s1")
    assert len(history) == 4
    assert history[0]["content"] == "Message 3"
    assert history[-1]["content"] == "Message 6"


def test_memory_session_cap_eviction() -> None:
    """Verify least-recently accessed session is evicted when max_sessions is reached."""
    current_time = 100.0

    def fake_clock() -> float:
        return current_time

    memory = ShortTermMemory(max_sessions=3, ttl_seconds=3600.0, clock=fake_clock)

    current_time = 100.0
    memory.add_turn(elder_id=1, session_id="s1", role="user", content="Turn 1")

    current_time = 200.0
    memory.add_turn(elder_id=2, session_id="s2", role="user", content="Turn 2")

    current_time = 300.0
    memory.add_turn(elder_id=3, session_id="s3", role="user", content="Turn 3")

    assert len(memory._sessions) == 3
    assert (1, "s1") in memory._sessions

    # Add 4th session -> triggers eviction of oldest session (1, 's1')
    current_time = 400.0
    memory.add_turn(elder_id=4, session_id="s4", role="user", content="Turn 4")

    assert len(memory._sessions) == 3
    assert (1, "s1") not in memory._sessions
    assert (2, "s2") in memory._sessions
    assert (3, "s3") in memory._sessions
    assert (4, "s4") in memory._sessions


def test_clear_session_public() -> None:
    """Verify clear_session empties session state."""
    memory = ShortTermMemory()
    memory.add_turn(elder_id=5, session_id="call-99", role="user", content="Hello")
    assert len(memory.get_history(elder_id=5, session_id="call-99")) == 1

    memory.clear_session(elder_id=5, session_id="call-99")
    assert memory.get_history(elder_id=5, session_id="call-99") == []


# ==============================================================================
# 3. CONVERSATION SERVICE RESILIENCE & ERROR HANDLING TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_provider_failure_with_emergency_text() -> None:
    """Verify provider failure on emergency text upgrades to HELP and returns safe neutral reply."""
    fake_llm = FakeLLM(error_to_raise=ProviderError("Sarvam LLM down", provider_name="SarvamLLM"))
    classifier = IntentClassifier(llm=fake_llm)
    service = ConversationService(classifier=classifier)

    result = await service.process_turn(
        elder_id=10,
        session_id="session-sos",
        user_text="Help, I fell down in the bathroom!",
        profile_context={"preferred_language": "en-IN"},
    )

    assert isinstance(result, ConverseResult)
    assert result.intent == Intent.HELP
    assert result.reply == "Are you okay? Tell me what happened."
    assert result.is_safe is True
    assert result.violations == []


@pytest.mark.asyncio
async def test_provider_failure_with_normal_text() -> None:
    """Verify provider failure on normal text returns language-aware trouble message."""
    fake_llm = FakeLLM(error_to_raise=ProviderError("Connection timeout", provider_name="SarvamLLM"))
    classifier = IntentClassifier(llm=fake_llm)
    service = ConversationService(classifier=classifier)

    result = await service.process_turn(
        elder_id=10,
        session_id="session-normal",
        user_text="How is your day going?",
        profile_context={"preferred_language": "hi-IN"},
    )

    assert isinstance(result, ConverseResult)
    assert result.intent == Intent.UNKNOWN
    assert result.reply == TROUBLE_CONNECTING_MESSAGES["hi-IN"]
    assert result.language == "hi-IN"

    # Verify failed turns are NOT added to memory
    history = service.memory.get_history(elder_id=10, session_id="session-normal")
    assert history == []


@pytest.mark.asyncio
async def test_emergency_with_low_confidence_never_repeats() -> None:
    """Verify emergency intent with low confidence never applies 'please repeat' fallback."""
    low_conf_llm = FakeLLM(
        default_response='{"intent": "sos", "reply": "I am here with you.", "confidence": 0.20}'
    )
    classifier = IntentClassifier(llm=low_conf_llm)
    service = ConversationService(classifier=classifier)

    result = await service.process_turn(
        elder_id=12,
        session_id="session-sos-low",
        user_text="My chest hurts so much",
        profile_context={"preferred_language": "mr-IN"},
    )

    assert result.intent in (Intent.SOS, Intent.HELP)
    # Must NOT be a "please repeat" message
    assert result.reply != PLEASE_REPEAT_MESSAGES["mr-IN"]
    assert result.reply != PLEASE_REPEAT_MESSAGES["en-IN"]


@pytest.mark.asyncio
async def test_low_confidence_normal_intent_returns_repeat_reply() -> None:
    """Verify normal intent with confidence below threshold returns language-aware 'please repeat'."""
    low_conf_llm = FakeLLM(
        default_response='{"intent": "talk", "reply": "I see.", "confidence": 0.45}'
    )
    classifier = IntentClassifier(llm=low_conf_llm)
    service = ConversationService(classifier=classifier)

    result = await service.process_turn(
        elder_id=14,
        session_id="session-talk-low",
        user_text="Mumble mumble garden",
        profile_context={"preferred_language": "hi-IN"},
    )

    assert result.intent == Intent.TALK
    assert result.reply == PLEASE_REPEAT_MESSAGES["hi-IN"]
    assert result.confidence < CONFIDENCE_THRESHOLD

    # Verify "please repeat" turns are NOT stored in memory
    history = service.memory.get_history(elder_id=14, session_id="session-talk-low")
    assert history == []


@pytest.mark.asyncio
async def test_emergency_keyword_triggered_flag() -> None:
    """Verify emergency_keyword_triggered flag is True only when keyword causes an upgrade."""
    # LLM misclassifies fall as "talk"
    talk_llm = FakeLLM(
        default_response='{"intent": "talk", "reply": "Tell me more about your day.", "confidence": 0.95}'
    )
    classifier = IntentClassifier(llm=talk_llm)
    service = ConversationService(classifier=classifier)

    # 1. Triggered case
    res1 = await service.process_turn(
        elder_id=15,
        session_id="s-upgrade",
        user_text="I was walking and I fell down hard.",
    )
    assert res1.intent == Intent.HELP
    assert res1.emergency_keyword_triggered is True

    # 2. Non-triggered case (normal talk stays talk)
    res2 = await service.process_turn(
        elder_id=15,
        session_id="s-normal",
        user_text="The garden flowers look beautiful today.",
    )
    assert res2.intent == Intent.TALK
    assert res2.emergency_keyword_triggered is False


@pytest.mark.asyncio
async def test_multi_turn_memory_flow() -> None:
    """Verify valid multi-turn conversations persist turns in memory."""
    fake_llm = FakeLLM(
        default_response='{"intent": "talk", "reply": "I am doing well, thank you!", "confidence": 0.95}'
    )
    classifier = IntentClassifier(llm=fake_llm)
    service = ConversationService(classifier=classifier)

    await service.process_turn(
        elder_id=20,
        session_id="turn-session",
        user_text="Good morning Oldy Buddy!",
    )

    history = service.memory.get_history(elder_id=20, session_id="turn-session")
    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "Good morning Oldy Buddy!"}
    assert history[1] == {"role": "assistant", "content": "I am doing well, thank you!"}
