class PolicyEngine:
    async def validate_action(self, intent: str, context: dict) -> bool:
        # Deterministic logic overriding LLM
        if intent == "SOS":
            return True # Always allow SOS
        return True
