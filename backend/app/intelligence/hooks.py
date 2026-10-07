"""Event hooks for intelligence layer integrations with decision engine and other modules."""

from app.core.contracts import Intent


async def on_emergency_intent(
    elder_id: int,
    intent: Intent,
    session_id: str,
    keyword_triggered: bool,
) -> None:
    """Hook invoked when an emergency intent (SOS or HELP) is classified or upgraded.

    Note: This is a no-op hook for M3; decision logic and alerts are handled by M5.
    Must NOT claim any alert was sent.
    """
    # TODO(M5): publish event to events/decision engine module (Gayatri)
    pass
