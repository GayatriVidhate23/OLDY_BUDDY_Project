"""Intent classifier for elderly care conversations."""

import json
import re
from typing import Any, Optional

from app.core.contracts import Intent
from app.intelligence.base import LLMProvider
from app.intelligence.factory import get_providers
from app.intelligence.schemas import IntentClassificationResult

SYSTEM_PROMPT = """You are Oldy Buddy, a warm, respectful, and caring AI companion for elderly individuals.
Your task is to converse with the user and classify their intent into exactly ONE of the following 7 categories:

1. "talk": Casual conversation, greetings, sharing feelings, asking how you are, reminiscing, or small talk.
2. "help": Non-emergency assistance requests (e.g. help with daily chores, reaching an object, tech assistance).
3. "reminder_done": Confirming that they took their medication, completed a routine, or finished a reminder task.
4. "reminder_forgot": Stating that they forgot, missed, or haven't taken their medication/task yet.
5. "food": Requesting meals, food, tea, groceries, or expressing hunger.
6. "sos": Acute distress, severe pain, falls, chest pain, difficulty breathing, or urgent emergency calls for help.
7. "unknown": Ambiguous, unintelligible, gibberish, or unclear statements.

IMPORTANT GUIDELINES:
- Your reply must be compassionate, clear, brief, and senior-friendly.
- Never diagnose medical conditions or prescribe treatments.
- Return ONLY a valid JSON object matching this schema:
{
  "intent": "talk" | "help" | "reminder_done" | "reminder_forgot" | "food" | "sos" | "unknown",
  "reply": "Warm conversational response to the user",
  "confidence": 0.95,
  "reasoning": "Short explanation of classification"
}
"""

FALLBACK_REPLY = "I'm sorry, I didn't quite catch that. Could you please say that again?"


class IntentClassifier:
    """Classifies user speech into structured Intent and generates conversational reply."""

    def __init__(self, llm: Optional[LLMProvider] = None) -> None:
        self.llm = llm or get_providers().llm

    async def classify(
        self,
        user_text: str,
        conversation_history: Optional[list[dict[str, str]]] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> IntentClassificationResult:
        """Classify user text and generate a conversational reply.

        Args:
            user_text: The latest utterance from the elderly user.
            conversation_history: Optional previous chat turns [{'role': 'user'|'assistant', 'content': '...'}].
            context: Optional user context (e.g., active reminders, routine details).

        Returns:
            IntentClassificationResult with intent, reply, confidence, and reasoning.
        """
        clean_text = user_text.strip() if user_text else ""
        if not clean_text:
            return IntentClassificationResult(
                intent=Intent.UNKNOWN,
                reply="I didn't hear anything. How can I help you today?",
                confidence=0.0,
                reasoning="Empty user input",
            )

        messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

        if context:
            context_str = json.dumps(context, ensure_ascii=False)
            messages.append({
                "role": "system",
                "content": f"Active User Context (reminders/routines): {context_str}",
            })

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": clean_text})

        try:
            raw_response = await self.llm.complete(messages, temperature=0.1)
            return self._parse_response(raw_response)
        except Exception:
            return IntentClassificationResult(
                intent=Intent.UNKNOWN,
                reply=FALLBACK_REPLY,
                confidence=0.0,
                reasoning="Provider error or unhandled exception during classification",
            )

    def _parse_response(self, raw_text: str) -> IntentClassificationResult:
        """Parse and validate LLM output into IntentClassificationResult."""
        cleaned = raw_text.strip()
        # Strip markdown json wrappers if present
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()

        try:
            return IntentClassificationResult.model_validate_json(cleaned)
        except Exception:
            # Attempt to extract first JSON object if surrounded by extra text
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return IntentClassificationResult.model_validate_json(match.group(0))
                except Exception:
                    pass

            return IntentClassificationResult(
                intent=Intent.UNKNOWN,
                reply=FALLBACK_REPLY,
                confidence=0.0,
                reasoning="Failed to parse LLM JSON response",
            )
