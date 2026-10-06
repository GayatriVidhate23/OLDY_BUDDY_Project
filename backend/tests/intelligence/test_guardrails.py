"""Unit tests for safety guardrails and deterministic emergency keyword checking."""

import pytest
from app.core.contracts import Intent
from app.intelligence.guardrails import (
    apply_guardrails,
    check_emergency_keyword_upgrade,
    normalize_text,
    NEUTRAL_EMERGENCY_REPLY,
    MEDICAL_SAFETY_FALLBACK,
)


# ==============================================================================
# 1. TEXT NORMALIZATION TESTS
# ==============================================================================

@pytest.mark.parametrize(
    "raw_input, expected_normalized",
    [
        ("  Hello, World!  ", "hello world"),
        ("I CAN'T BREATHE...", "i can t breathe"),
        ("मदद करो! मुझे दर्द है।", "मदद करो मुझे दर्द है"),
        ("मी खाली पडलो... वाचवा!", "मी खाली पडलो वाचवा"),
        ("Café \u0065\u0301", "café é"),  # Unicode NFD to NFC
        ("", ""),
        ("   \t\n  ", ""),
    ],
)
def test_normalize_text(raw_input: str, expected_normalized: str) -> None:
    """Verify that normalization properly handles NFC, casing, and punctuation."""
    assert normalize_text(raw_input) == expected_normalized


# ==============================================================================
# 2. PARAMETRIZED STRONG TIER KEYWORD UPGRADE TESTS
# ==============================================================================

STRONG_EMERGENCY_CASES = [
    # English
    "I fell down on the floor!",
    "Help, I fall down in the bathroom.",
    "I have severe chest pain right now.",
    "Pain in my chest is getting worse.",
    "I can't breathe properly.",
    "I cannot breathe at all.",
    "I feel like I am unable to breathe.",
    "He suddenly became unconscious.",
    "I fainted in the kitchen.",
    # Hindi (Masculine & Feminine forms)
    "मैं कमरे में गिर गया!",
    "मैं रसोई में गिर गई जोर से।",
    "दादाजी सीढ़ियों से गिर पड़े।",
    "दादीजी फर्श पर गिर पड़ीं।",
    "मेरे सीने में दर्द हो रहा है।",
    "मेरी छाती में दर्द बहुत तेज है।",
    "मुझे सांस नहीं आ रही है।",
    "मुझे सांस लेने में तकलीफ हो रही है।",
    "वह अचानक बेहोश हो गए।",
    # Marathi (Masculine & Feminine forms)
    "मी रात्री खाली पडलो!",
    "मी बागेत चक्कर येऊन खाली पडले.",
    "माझ्या छातीत दुखतंय खूप.",
    "माझ्या छातीत दुखत आहे जोरात.",
    "मला श्वास घेता येत नाहीये.",
    "मला खूप दम लागतोय श्वास लागतोय.",
    "मला अचानक भोवळ आली आणि पडले.",
]


@pytest.mark.parametrize("user_text", STRONG_EMERGENCY_CASES)
@pytest.mark.parametrize(
    "initial_intent",
    [Intent.TALK, Intent.UNKNOWN, Intent.REMINDER_DONE, Intent.REMINDER_FORGOT, Intent.FOOD],
)
def test_strong_tier_upgrades_all_intents_to_help(user_text: str, initial_intent: Intent) -> None:
    """Verify STRONG tier emergencies upgrade ANY intent except SOS/HELP to HELP."""
    result = check_emergency_keyword_upgrade(user_text, current_intent=initial_intent)
    assert result == Intent.HELP


@pytest.mark.parametrize("user_text", STRONG_EMERGENCY_CASES)
@pytest.mark.parametrize("protected_intent", [Intent.SOS, Intent.HELP])
def test_strong_tier_never_downgrades_sos_or_help(user_text: str, protected_intent: Intent) -> None:
    """Verify STRONG tier keywords never alter or downgrade SOS or HELP intents."""
    result = check_emergency_keyword_upgrade(user_text, current_intent=protected_intent)
    assert result == protected_intent


# ==============================================================================
# 3. PARAMETRIZED WEAK TIER KEYWORD UPGRADE TESTS
# ==============================================================================

WEAK_EMERGENCY_CASES = [
    # English
    "Please help me with this jar.",
    "I am in severe pain today.",
    "My finger is bleeding.",
    "My knee hurts badly.",
    "I am in trouble here.",
    # Hindi
    "मेरी मदद करो कोई!",
    "मुझे सिर में बहुत दर्द है।",
    "मुझे बहुत चक्कर आ रहे हैं।",
    "मुझे बहुत तकलीफ हो रही है।",
    "बचाओ मुझे!",
    # Marathi
    "माझी मदत करा कृपया.",
    "मला आज खूप त्रास होतोय.",
    "माझे पाय दुखतंय खूप.",
    "वाचवा मला!",
]


@pytest.mark.parametrize("user_text", WEAK_EMERGENCY_CASES)
@pytest.mark.parametrize("upgradeable_intent", [Intent.TALK, Intent.UNKNOWN])
def test_weak_tier_upgrades_talk_and_unknown_to_help(user_text: str, upgradeable_intent: Intent) -> None:
    """Verify WEAK tier keywords upgrade TALK and UNKNOWN intents to HELP."""
    result = check_emergency_keyword_upgrade(user_text, current_intent=upgradeable_intent)
    assert result == Intent.HELP


@pytest.mark.parametrize("user_text", WEAK_EMERGENCY_CASES)
@pytest.mark.parametrize(
    "preserved_intent",
    [Intent.REMINDER_DONE, Intent.REMINDER_FORGOT, Intent.FOOD, Intent.SOS, Intent.HELP],
)
def test_weak_tier_preserves_specific_and_protected_intents(
    user_text: str, preserved_intent: Intent
) -> None:
    """Verify WEAK tier keywords do NOT overwrite domain intents (reminders, food) or SOS/HELP."""
    result = check_emergency_keyword_upgrade(user_text, current_intent=preserved_intent)
    assert result == preserved_intent


# ==============================================================================
# 4. FALSE POSITIVE PREVENTION TESTS (BARE STEMS & EVERYDAY CONVERSATION)
# ==============================================================================

FALSE_POSITIVE_CASES = [
    # English ("fell asleep", "fall weather", general talk)
    "I fell asleep on the sofa after lunch.",
    "I fell asleep while reading a book.",
    "I love the cool weather in the fall season.",
    "I had a nice talk with my granddaughter today.",
    "The morning sunlight was very pleasant.",
    # Marathi ("पाऊस पडतोय", etc. - avoiding bare "पड")
    "बाहेर खूप छान पाऊस पडतोय आज.",
    "पाऊस पडतोय त्यामुळे गारवा आहे.",
    "मी आज छान चहा पिला आणि वर्तमानपत्र वाचले.",
    # Hindi ("पत्ते गिर रहे हैं", etc. - avoiding bare "गिर")
    "बगीचे में पेड़ से सूखे पत्ते गिर रहे हैं।",
    "पेड़ से आम नीचे गिर रहे हैं।",
    "मैंने आज सुबह की दवा समय पर ले ली।",
]


@pytest.mark.parametrize("normal_text", FALSE_POSITIVE_CASES)
def test_false_positive_cases_do_not_upgrade_talk(normal_text: str) -> None:
    """Verify normal conversations and bare stem phrases do NOT trigger false upgrades."""
    result = check_emergency_keyword_upgrade(normal_text, current_intent=Intent.TALK)
    assert result == Intent.TALK


# ==============================================================================
# 5. GUARDRAIL REPLY SANITIZATION TESTS
# ==============================================================================

def test_allowed_phrasings_not_blocked() -> None:
    """Verify that everyday companion replies are NOT blocked by guardrails."""
    allowed_replies = [
        "Good morning! How are you feeling today?",
        "I am so glad you took your morning medicine on time.",
        "Did you get a chance to do your light stretching routine?",
        "I can help you request dinner from the kitchen.",
        "The weather is lovely outside for a short walk.",
        "Would you like me to tell you a story or play some music?",
        "Don't forget to drink a glass of water with your lunch.",
    ]

    for reply in allowed_replies:
        result = apply_guardrails(reply, intent=Intent.TALK)
        assert result.is_safe is True
        assert result.sanitized_reply == reply
        assert result.violations == []
        assert result.fallback_triggered is False


def test_medical_diagnosis_blocked() -> None:
    """Verify that attempting to diagnose medical conditions is blocked and sanitized."""
    diagnostic_replies = [
        "You have pneumonia, you need to rest.",
        "Sounds like you have bronchitis based on your cough.",
        "This is definitely a stroke, you have severe illness.",
        "My diagnosis is that you are suffering from hypertension.",
        "You have diabetes which is why you feel dizzy.",
    ]

    for reply in diagnostic_replies:
        result = apply_guardrails(reply, intent=Intent.TALK)
        assert result.is_safe is False
        assert result.sanitized_reply == MEDICAL_SAFETY_FALLBACK
        assert "medical_diagnosis" in result.violations
        assert result.fallback_triggered is True


def test_medical_prescription_and_dosage_blocked() -> None:
    """Verify that suggesting medications or altering dosages is blocked and sanitized."""
    prescription_replies = [
        "Take 500mg aspirin right now for your headache.",
        "Double your insulin dose before going to sleep.",
        "Stop taking your blood pressure tablets if you feel fine.",
        "I prescribe 20mg paracetamol for the fever.",
        "Administer a dose of 10ml cough syrup immediately.",
    ]

    for reply in prescription_replies:
        result = apply_guardrails(reply, intent=Intent.TALK)
        assert result.is_safe is False
        assert result.sanitized_reply == MEDICAL_SAFETY_FALLBACK
        assert "medical_prescription" in result.violations
        assert result.fallback_triggered is True


def test_unauthorized_alert_claims_blocked_for_sos_and_help() -> None:
    """Verify that the AI never claims an alert was sent; neutral safe reply is enforced."""
    alert_claim_replies = [
        "I have alerted your caregiver and family right away.",
        "Don't worry, help is on the way and an ambulance is coming.",
        "I notified the emergency services and police.",
        "I called 108 for you, stay calm.",
    ]

    for reply in alert_claim_replies:
        result = apply_guardrails(reply, intent=Intent.SOS)
        assert result.is_safe is False
        assert result.sanitized_reply == NEUTRAL_EMERGENCY_REPLY
        assert "unauthorized_alert_claim" in result.violations
        assert result.fallback_triggered is True


def test_sos_and_help_neutral_reply_preserved() -> None:
    """Verify neutral emergency replies pass through safely for SOS/HELP."""
    result = apply_guardrails("Are you okay? Tell me what happened.", intent=Intent.SOS)
    assert result.is_safe is True
    assert result.sanitized_reply == "Are you okay? Tell me what happened."
    assert result.violations == []
