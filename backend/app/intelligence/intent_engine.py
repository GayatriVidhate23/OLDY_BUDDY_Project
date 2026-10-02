class IntentEngine:
    async def infer_intent(self, user_input: str) -> str:
        # Mock LLM interaction
        if "help" in user_input.lower() or "sos" in user_input.lower():
            return "SOS"
        return "GENERAL"
