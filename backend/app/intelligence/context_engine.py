class ContextEngine:
    async def get_context(self, elder_id: int, db) -> dict:
        # Mock fetch from DB/Redis
        return {"current_mood": "calm", "last_activity": "medicine"}
