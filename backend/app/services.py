from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from app.models import User, ElderProfile, Activity
from app.schemas import UserCreate, ElderProfileBase, ActivityBase
from app.auth import get_password_hash

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already exists")
    user = User(email=user_in.email, hashed_password=get_password_hash(user_in.password), full_name=user_in.full_name, role=user_in.role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_profile(db: AsyncSession, elder_id: int) -> ElderProfile:
    result = await db.execute(select(ElderProfile).where(ElderProfile.user_id == elder_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

async def create_activity(db: AsyncSession, elder_id: int, activity_in: ActivityBase) -> Activity:
    activity = Activity(**activity_in.model_dump(), elder_id=elder_id)
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    # Simple workflow logic inside service
    if activity.activity_type == "SOS":
        print(f"SOS triggered for elder {elder_id} - notifying caregivers!")
    return activity

from app.models import CallRecord
from datetime import datetime, timezone

async def initiate_call(db: AsyncSession, elder_id: int, call_type: str) -> CallRecord:
    # 1. Create call record
    record = CallRecord(elder_id=elder_id, call_type=call_type, status="INITIATED")
    db.add(record)
    await db.commit()
    await db.refresh(record)
    
    # 2. Mock Telephony Provider Call
    print(f"[TELEPHONY MOCK] Calling Elder {elder_id} for {call_type}. Call ID: {record.id}")
    return record

async def process_voice_webhook(db: AsyncSession, call_id: int, event_type: str, speech_text: str = None):
    result = await db.execute(select(CallRecord).where(CallRecord.id == call_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Call record not found")

    if event_type == "answered":
        record.status = "IN_PROGRESS"
    
    elif event_type == "speech" and speech_text:
        text = speech_text.lower()
        # Mock Intent/Policy Engine for Safety
        if "help" in text or "sos" in text or "emergency" in text:
            record.response = "NEED_HELP"
            record.outcome = "ESCALATED"
            record.status = "COMPLETED"
            # Trigger SOS Activity directly (Policy Engine safety rule: LLM doesn't decide this)
            act = Activity(elder_id=record.elder_id, activity_type="SOS", description=f"Triggered via voice call {call_id}: {speech_text}")
            db.add(act)
            print(f"[POLICY] SOS Triggered for Elder {record.elder_id} from Voice Call")
        elif "yes" in text:
            record.response = "YES"
            record.outcome = "COMPLETED_SUCCESS"
        elif "no" in text:
            record.response = "NO"
            record.outcome = "NEEDS_FOLLOWUP"
            
    elif event_type in ["completed", "failed"]:
        record.status = event_type.upper()
        record.end_time = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(record)
    return {"status": "ok", "record": record}
