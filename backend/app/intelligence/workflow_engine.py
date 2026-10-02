from app.models.activity import Activity
from app.intelligence.context_engine import ContextEngine
from app.intelligence.policy_engine import PolicyEngine

context_engine = ContextEngine()
policy_engine = PolicyEngine()

async def process_activity(activity: Activity, db):
    context = await context_engine.get_context(activity.elder_id, db)
    # Perform deterministic checks and side effects (like sending notifications)
    is_valid = await policy_engine.validate_action(activity.activity_type, context)
    if is_valid and activity.activity_type == "SOS":
        # e.g., create alert, send notification
        pass
