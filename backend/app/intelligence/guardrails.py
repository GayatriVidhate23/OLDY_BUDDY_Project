"""Safety guardrails and deterministic keyword checking for Oldy Buddy conversational AI."""

import re
from typing import Optional
import unicodedata

from app.core.contracts import Intent
from app.intelligence.schemas import GuardrailResult

# Standard neutral replies
NEUTRAL_EMERGENCY_REPLY = "Are you okay? Tell me what happened."
MEDICAL_SAFETY_FALLBACK = (
    "I cannot give medical advice or diagnose health conditions. "
    "Please speak with your doctor or caregiver about your symptoms."
)


def normalize_text(text: str) -> str:
    """Normalize text using Unicode NFC, lowercase, and punctuation stripping.

    Preserves letters and combining marks across Latin and Indic scripts (Hindi/Marathi).
    """
    if not text:
        return ""
    # 1. Unicode NFC normalization and lowercasing
    nfc_text = unicodedata.normalize("NFC", text).lower()
    # 2. Replace all Unicode punctuation (categories starting with 'P' or 'S') with spaces
    cleaned = "".join(" " if unicodedata.category(c).startswith(("P", "S")) else c for c in nfc_text)
    # 3. Collapse multiple whitespace characters into single spaces
    return " ".join(cleaned.split())


# ==============================================================================
# TWO KEYWORD TIERS (in one place): STRONG and WEAK
# ==============================================================================

# STRONG: Acute emergencies (fall, chest pain, breathing trouble, unconsciousness).
# Upgrades ANY intent (except SOS and HELP) to HELP. Never downgrades SOS or HELP.
# Uses (?<!\S) ... (?!\S) for script-agnostic word/phrase boundary matching.
STRONG_EMERGENCY_PATTERNS: tuple[re.Pattern, ...] = (
    # English (specific phrases avoiding bare "fell" / "fall")
    re.compile(r"(?<!\S)(fell down|fall down|fallen down)(?!\S)"),
    re.compile(r"(?<!\S)(chest pain|pain in (?:my )?chest)(?!\S)"),
    re.compile(r"(?<!\S)(can t breathe|cant breathe|cannot breathe|unable to breathe|hard to breathe|trouble breathing)(?!\S)"),
    re.compile(r"(?<!\S)(unconscious|fainted|loss of consciousness|passed out)(?!\S)"),
    # Hindi: masculine & feminine forms, specific phrases (avoid bare "गिर")
    re.compile(r"(?<!\S)(गिर गया|गिर गई|गिर पड़े|गिर पड़[ीिं]+)(?!\S)"),
    re.compile(r"(?<!\S)(छाती में दर्द|सीने में दर्द)(?!\S)"),
    re.compile(r"(?<!\S)(सांस नहीं|सांस लेने में (?:दिक्कत|तकलीफ)|सांस फूल रही)(?!\S)"),
    re.compile(r"(?<!\S)(बेहोश|बेहोशी)(?!\S)"),
    # Marathi: masculine & feminine forms, specific phrases (avoid bare "पड")
    re.compile(r"(?<!\S)(खाली पडलो|खाली पडले|पडलो|पडले)(?!\S)"),
    re.compile(r"(?<!\S)(छातीत दुखतंय|छातीत दुखत आहे|छातीत कळ)(?!\S)"),
    re.compile(r"(?<!\S)(श्वास घेता येत नाही(?:ये)?|श्वास लागतोय|दम लागतोय)(?!\S)"),
    re.compile(r"(?<!\S)(भोवळ|बेहोश)(?!\S)"),
)

# WEAK: General distress, assistance, or discomfort (pain, help, trouble).
# Upgrades ONLY TALK and UNKNOWN intents to HELP. Preserves specific domain intents (reminders, food).
WEAK_EMERGENCY_PATTERNS: tuple[re.Pattern, ...] = (
    # English
    re.compile(r"(?<!\S)(help|emergency|severe pain|in pain|hurts badly|bleeding|injured|need assistance|trouble)(?!\S)"),
    # Hindi
    re.compile(r"(?<!\S)(मदद|बचाओ|दर्द|चक्कर|तकलीफ)(?!\S)"),
    # Marathi
    re.compile(r"(?<!\S)(मदत|वाचवा|दुखतंय|दुखतय|त्रास)(?!\S)"),
)


# ==============================================================================
# MEDICAL & ALERT CLAIM GUARDRAIL PATTERNS (for sanitizing reply text)
# ==============================================================================

# Medical Diagnosis patterns (forbidden in AI reply)
DIAGNOSIS_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(
        r"\b(you have|diagnosed with|suffering from|sounds like (?:you have )?|you might have|this is(?:\s+\w+)?)\s+"
        r"(?:a\s+|an\s+)?(bronchitis|pneumonia|covid|diabetes|hypertension|heart failure|stroke|heart attack|cancer|depression|dementia|infection)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(my diagnosis is|medical diagnosis|clinically speaking)\b", re.IGNORECASE),
)

# Medical Prescription / Dosage modification patterns (forbidden in AI reply)
PRESCRIPTION_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"\b(prescribe|prescribing)\b", re.IGNORECASE),
    re.compile(
        r"\b(take|increase|decrease|double|stop taking|start taking|administer|skip)\s+"
        r"(?:(?:your|a|the|some|more|less)\s+)*"
        r"(?:(?:dose|dosage)\s+of\s+)?"
        r"(?:\d+\s*(?:mg|ml|mcg|grams?|tablets?|pills?)\s+(?:of\s+)?)?"
        r"(?:[\w-]+\s+)*"
        r"(aspirin|paracetamol|ibuprofen|tylenol|insulin|metformin|antibiotics|warfarin|atorvastatin|amlodipine|lisinopril|cough syrup|pills|tablets|medicine|medication|dose|dosage)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(dosage of|dose of)\s+\d+\s*(mg|ml|mcg|tablets?|pills?)\b", re.IGNORECASE),
)

# Claims of sending alerts or knowing danger (forbidden in AI reply)
ALERT_CLAIM_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(
        r"\b(i (have )?(alerted|notified|called|contacted)|alert(ing)?|notif(ying)?)\s+"
        r"(the|your)?\s*(caregiver|family|doctor|police|ambulance|authorities|emergency services)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(help is on the way|an ambulance is coming|i called 911|i called 108|i called 112)\b", re.IGNORECASE),
    re.compile(r"\b(i know you are (dying|in danger|having a stroke))\b", re.IGNORECASE),
)


def check_emergency_keyword_upgrade(user_text: str, current_intent: Intent) -> Intent:
    """Deterministically upgrade intent based on two-tier emergency keyword rules.

    Rules:
    - Never downgrade Intent.SOS or Intent.HELP.
    - STRONG keywords (fall, chest pain, can't breathe, unconscious) upgrade ANY intent
      except SOS/HELP to Intent.HELP.
    - WEAK keywords (pain, trouble, help) upgrade ONLY TALK and UNKNOWN intents to Intent.HELP.
    - Input is normalized (Unicode NFC, lowercase, punctuation stripped) before matching.
    """
    if current_intent in (Intent.SOS, Intent.HELP):
        return current_intent

    normalized = normalize_text(user_text)
    if not normalized:
        return current_intent

    # Check Tier 1: STRONG emergency keywords (upgrades any intent to HELP)
    for pattern in STRONG_EMERGENCY_PATTERNS:
        if pattern.search(normalized):
            return Intent.HELP

    # Check Tier 2: WEAK emergency keywords (upgrades only TALK and UNKNOWN to HELP)
    if current_intent in (Intent.TALK, Intent.UNKNOWN):
        for pattern in WEAK_EMERGENCY_PATTERNS:
            if pattern.search(normalized):
                return Intent.HELP

    return current_intent


def apply_guardrails(reply: str, intent: Optional[Intent] = None) -> GuardrailResult:
    """Apply safety guardrails to AI-generated reply.

    Guardrails modify reply text only and never change the intent.

    Args:
        reply: Raw conversational reply from LLM.
        intent: Classified Intent.

    Returns:
        GuardrailResult with sanitized reply and any violation tags.
    """
    cleaned_reply = reply.strip() if reply else ""
    violations: list[str] = []

    # 1. For SOS / HELP intents: use neutral phrasing and ensure no false alert claims
    if intent in (Intent.SOS, Intent.HELP):
        has_alert_claim = any(p.search(cleaned_reply) for p in ALERT_CLAIM_PATTERNS)
        if has_alert_claim:
            violations.append("unauthorized_alert_claim")
            return GuardrailResult(
                is_safe=False,
                sanitized_reply=NEUTRAL_EMERGENCY_REPLY,
                violations=violations,
                fallback_triggered=True,
            )

        if not cleaned_reply:
            return GuardrailResult(
                is_safe=True,
                sanitized_reply=NEUTRAL_EMERGENCY_REPLY,
                violations=[],
                fallback_triggered=True,
            )

    # 2. Check for unauthorized alert claims in any intent
    for pattern in ALERT_CLAIM_PATTERNS:
        if pattern.search(cleaned_reply):
            violations.append("unauthorized_alert_claim")
            return GuardrailResult(
                is_safe=False,
                sanitized_reply=NEUTRAL_EMERGENCY_REPLY if intent in (Intent.SOS, Intent.HELP) else "I am here with you. How can I assist you right now?",
                violations=violations,
                fallback_triggered=True,
            )

    # 3. Check for medical diagnosis attempts
    for pattern in DIAGNOSIS_PATTERNS:
        if pattern.search(cleaned_reply):
            violations.append("medical_diagnosis")
            return GuardrailResult(
                is_safe=False,
                sanitized_reply=MEDICAL_SAFETY_FALLBACK,
                violations=violations,
                fallback_triggered=True,
            )

    # 4. Check for medical prescription / dosage modification attempts
    for pattern in PRESCRIPTION_PATTERNS:
        if pattern.search(cleaned_reply):
            violations.append("medical_prescription")
            return GuardrailResult(
                is_safe=False,
                sanitized_reply=MEDICAL_SAFETY_FALLBACK,
                violations=violations,
                fallback_triggered=True,
            )

    # Safe - return original cleaned reply
    return GuardrailResult(
        is_safe=True,
        sanitized_reply=cleaned_reply or "How can I help you?",
        violations=[],
        fallback_triggered=False,
    )
