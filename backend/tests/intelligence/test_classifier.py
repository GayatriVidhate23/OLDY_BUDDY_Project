"""Unit tests for IntentClassifier."""

import json
import pytest
from app.core.contracts import Intent
from app.intelligence.classifier import IntentClassifier, FALLBACK_REPLY
from app.intelligence.exceptions import ProviderError
from app.intelligence.fake import FakeLLM
from app.intelligence.schemas import IntentClassificationResult


@pytest.mark.asyncio
async def test_classify_all_intents() -> None:
    """Verify classification across all standard Intent types."""
    test_cases = [
        (
            Intent.TALK,
            '{"intent": "talk", "reply": "Good morning! I am doing well, thank you.", "confidence": 0.98, "reasoning": "Elder sharing greetings"}',
            "Good morning, how are you?",
        ),
        (
            Intent.HELP,
            '{"intent": "help", "reply": "I can assist with that. What do you need help with?", "confidence": 0.95, "reasoning": "Asking for household help"}',
            "Can someone help me reach the top shelf?",
        ),
        (
            Intent.REMINDER_DONE,
            '{"intent": "reminder_done", "reply": "Wonderful! I will mark your morning pills as taken.", "confidence": 0.99, "reasoning": "Confirmed medication taken"}',
            "I just took my blood pressure tablet.",
        ),
        (
            Intent.REMINDER_FORGOT,
            '{"intent": "reminder_forgot", "reply": "No problem, please take your medicine now with a glass of water.", "confidence": 0.92, "reasoning": "Elder forgot medication"}',
            "Oh dear, I forgot to take my pills today.",
        ),
        (
            Intent.FOOD,
            '{"intent": "food", "reply": "Let me help you request lunch. What would you like to eat?", "confidence": 0.96, "reasoning": "Food request"}',
            "I'm feeling hungry, what's for lunch?",
        ),
        (
            Intent.SOS,
            '{"intent": "sos", "reply": "Please stay still. I am alerting your caregiver right away.", "confidence": 0.99, "reasoning": "Elder reports a fall"}',
            "Help, I fell down in the bathroom!",
        ),
        (
            Intent.UNKNOWN,
            '{"intent": "unknown", "reply": "I did not understand that. Could you say it again?", "confidence": 0.50, "reasoning": "Incoherent utterance"}',
            "Blah bleh foo bar",
        ),
    ]

    for expected_intent, canned_response, user_query in test_cases:
        fake_llm = FakeLLM(default_response=canned_response)
        classifier = IntentClassifier(llm=fake_llm)

        result = await classifier.classify(user_query)

        assert isinstance(result, IntentClassificationResult)
        assert result.intent == expected_intent
        assert result.confidence > 0.0
        assert len(result.reply) > 0
        assert len(fake_llm.calls) == 1


@pytest.mark.asyncio
async def test_classify_markdown_wrapped_json() -> None:
    """Verify that classifier correctly parses markdown code block JSON."""
    markdown_json = """```json
{
  "intent": "food",
  "reply": "I can arrange some warm tea and snacks for you.",
  "confidence": 0.94,
  "reasoning": "Request for tea"
}
```"""
    fake_llm = FakeLLM(default_response=markdown_json)
    classifier = IntentClassifier(llm=fake_llm)

    result = await classifier.classify("I'd like some warm tea please.")

    assert result.intent == Intent.FOOD
    assert result.reply == "I can arrange some warm tea and snacks for you."
    assert result.confidence == 0.94


@pytest.mark.asyncio
async def test_classify_surrounding_text_json() -> None:
    """Verify that classifier extracts JSON embedded in conversational text."""
    wrapped_text = """Here is the structured classification:
{"intent": "talk", "reply": "I love hearing about your garden!", "confidence": 0.9}
Hope this helps!"""
    fake_llm = FakeLLM(default_response=wrapped_text)
    classifier = IntentClassifier(llm=fake_llm)

    result = await classifier.classify("The flowers are blooming today.")

    assert result.intent == Intent.TALK
    assert result.reply == "I love hearing about your garden!"
    assert result.confidence == 0.9


@pytest.mark.asyncio
async def test_classify_malformed_json_fallback() -> None:
    """Verify graceful fallback when LLM returns invalid JSON or non-JSON text."""
    invalid_outputs = [
        "Not a JSON string at all.",
        '{"intent": "invalid_intent_value", "reply": "hi"}',
        '{"missing_intent_key": 123}',
        "",
        "{broken_json:",
    ]

    for bad_output in invalid_outputs:
        fake_llm = FakeLLM(default_response=bad_output)
        classifier = IntentClassifier(llm=fake_llm)

        result = await classifier.classify("Hello there")

        assert result.intent == Intent.UNKNOWN
        assert result.reply == FALLBACK_REPLY
        assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_classify_empty_user_text() -> None:
    """Verify empty or whitespace user text returns UNKNOWN without calling LLM."""
    fake_llm = FakeLLM()
    classifier = IntentClassifier(llm=fake_llm)

    for empty_input in ["", "   ", "\n\t"]:
        result = await classifier.classify(empty_input)
        assert result.intent == Intent.UNKNOWN
        assert result.confidence == 0.0
        assert len(fake_llm.calls) == 0


@pytest.mark.asyncio
async def test_classify_provider_exception_handling() -> None:
    """Verify classifier catches provider errors and returns graceful fallback."""
    fake_llm = FakeLLM(error_to_raise=ProviderError("Rate limit exceeded", provider_name="FakeLLM"))
    classifier = IntentClassifier(llm=fake_llm)

    result = await classifier.classify("Hello?")

    assert result.intent == Intent.UNKNOWN
    assert result.reply == FALLBACK_REPLY
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_classify_with_history_and_context() -> None:
    """Verify conversation history and user context are passed to LLM messages."""
    fake_llm = FakeLLM(default_response='{"intent": "reminder_done", "reply": "Great!", "confidence": 1.0}')
    classifier = IntentClassifier(llm=fake_llm)

    history = [
        {"role": "assistant", "content": "Did you take your morning blood pressure pill?"}
    ]
    context = {"active_reminder": "Blood Pressure 10mg", "scheduled_time": "08:00"}

    result = await classifier.classify(
        user_text="Yes, just now.",
        conversation_history=history,
        context=context,
    )

    assert result.intent == Intent.REMINDER_DONE
    assert len(fake_llm.calls) == 1
    sent_messages = fake_llm.calls[0]["messages"]

    # System prompt + Context system message + History + Latest user message
    assert len(sent_messages) == 4
    assert "Active User Context" in sent_messages[1]["content"]
    assert json.dumps(context) in sent_messages[1]["content"] or "Blood Pressure" in sent_messages[1]["content"]
    assert sent_messages[2] == history[0]
    assert sent_messages[3] == {"role": "user", "content": "Yes, just now."}
