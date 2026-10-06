import os

base_backend = r"c:\Users\gayat\Documents\OLDY_BUDDY_Project\backend\app"

with open(os.path.join(base_backend, "api.py"), "r", encoding="utf-8") as f:
    api_content = f.read()

if "POST /elders/{elder_id}/chat" not in api_content:
    new_endpoints = """

from pydantic import BaseModel
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@router.post("/elders/{elder_id}/chat", response_model=ChatResponse)
async def chat_with_ai(elder_id: int, req: ChatRequest, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    # Log user message
    user_msg = Activity(elder_id=elder_id, activity_type="CONVERSATION", description=f"User: {req.message}", status="COMPLETED")
    db.add(user_msg)
    
    # Mock AI logic based on context (in a real app, query OpenAI with ElderProfile)
    reply_text = "I'm here for you! I've noted that down. Is there anything else you need help with?"
    if "help" in req.message.lower() or "emergency" in req.message.lower():
        reply_text = "I am triggering an SOS alert to your family immediately. Please stay safe."
        sos_msg = Activity(elder_id=elder_id, activity_type="SOS", description="Triggered via chat", status="PENDING")
        db.add(sos_msg)

    ai_msg = Activity(elder_id=elder_id, activity_type="CONVERSATION", description=f"AI: {reply_text}", status="COMPLETED")
    db.add(ai_msg)
    
    await db.commit()
    return ChatResponse(reply=reply_text)
"""
    with open(os.path.join(base_backend, "api.py"), "w", encoding="utf-8") as f:
        f.write(api_content + new_endpoints)

print("Backend chat API added.")
