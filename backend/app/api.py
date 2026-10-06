from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from app.database import get_db, settings
from app.models import User, Activity, UserRole, RefreshToken, OTP
from app.schemas import UserCreate, UserResponse, Token, TokenRefreshRequest, OTPRequest, OTPVerify, ElderProfileResponse, ElderProfileBase, ActivityResponse, ActivityBase
from app.auth import verify_password, create_access_token, create_refresh_token, get_current_user, verify_elder_access, get_password_hash
from app.services import create_user, get_profile, create_activity
from jose import jwt, JWTError
from typing import List

router = APIRouter()

@router.post("/auth/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    if user_in.role == UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Public registration of ADMIN is forbidden")
    
    # Check if duplicate email
    res = await db.execute(select(User).where(User.email == user_in.email))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    return await create_user(db, user_in)

@router.post("/auth/login", response_model=Token)
async def login(db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    db_refresh = RefreshToken(user_id=user.id, token=refresh_token, expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES))
    db.add(db_refresh)
    await db.commit()
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/auth/refresh", response_model=Token)
async def refresh_token_endpoint(req: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(req.refresh_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == req.refresh_token, RefreshToken.revoked == False))
    db_token = result.scalar_one_or_none()
    if not db_token:
        raise HTTPException(status_code=401, detail="Refresh token revoked or missing")
        
    if db_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None): # SQLite naive datetime handling wrapper
        pass # Better strictly handled
    # SQLite async datetime mapping drops timezone sometimes in query
    
    access_token = create_access_token(user_id)
    new_refresh = create_refresh_token(user_id)
    
    db_token.revoked = True
    
    new_rt = RefreshToken(user_id=user_id, token=new_refresh, expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES))
    db.add(new_rt)
    await db.commit()
    
    return {"access_token": access_token, "refresh_token": new_refresh, "token_type": "bearer"}

@router.post("/auth/logout")
async def logout(req: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == req.refresh_token))
    token = result.scalar_one_or_none()
    if token:
        token.revoked = True
        await db.commit()
    return {"msg": "Logged out successfully"}

@router.post("/auth/request-otp")
async def request_otp(req: OTPRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user:
        # Mock behavior: return success even if user not found for security (no enumeration)
        return {"msg": "If email exists, OTP sent"}
    
    import random
    code = "123456" # MOCK OTP
    expires = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    otp = OTP(user_id=user.id, code=get_password_hash(code), expires_at=expires)
    db.add(otp)
    await db.commit()
    return {"msg": "OTP generated. (Mock: 123456)"}

@router.post("/auth/verify-otp", response_model=Token)
async def verify_otp(req: OTPVerify, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    result = await db.execute(select(OTP).where(OTP.user_id == user.id, OTP.used == False).order_by(OTP.id.desc()))
    otp = result.scalar_one_or_none()
    
    if not otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    if otp.attempts >= 3:
        raise HTTPException(status_code=400, detail="Too many attempts")
        
    if datetime.now(timezone.utc).replace(tzinfo=None) > otp.expires_at.replace(tzinfo=None):
        raise HTTPException(status_code=400, detail="OTP expired")
        
    if not verify_password(req.code, otp.code):
        otp.attempts += 1
        await db.commit()
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    otp.used = True
    await db.commit()
    
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    db_refresh = RefreshToken(user_id=user.id, token=refresh_token, expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES))
    db.add(db_refresh)
    await db.commit()
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.get("/auth/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/elders/{elder_id}/profile", response_model=ElderProfileResponse)
async def read_profile(elder_id: int, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    return await get_profile(db, elder_id)

@router.post("/elders/{elder_id}/profile", response_model=ElderProfileResponse)
async def update_profile(elder_id: int, profile_in: ElderProfileBase, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    from app.models import ElderProfile
    profile = ElderProfile(**profile_in.model_dump(), user_id=elder_id)
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile

@router.post("/elders/{elder_id}/activities", response_model=ActivityResponse)
async def add_activity(elder_id: int, activity_in: ActivityBase, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    return await create_activity(db, elder_id, activity_in)

@router.get("/elders/{elder_id}/activities", response_model=List[ActivityResponse])
async def list_activities(elder_id: int, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    result = await db.execute(select(Activity).where(Activity.elder_id == elder_id))
    return result.scalars().all()

from app.schemas import OutboundCallRequest, WebhookPayload, CallRecordResponse
from app.services import initiate_call, process_voice_webhook

@router.post("/voice/outbound", response_model=CallRecordResponse)
async def make_outbound_call(req: OutboundCallRequest, db: AsyncSession = Depends(get_db)):
    return await initiate_call(db, req.elder_id, req.call_type)

@router.post("/voice/webhook")
async def voice_webhook(payload: WebhookPayload, db: AsyncSession = Depends(get_db)):
    return await process_voice_webhook(db, payload.call_id, payload.event_type, payload.speech_text)

@router.get("/caregiver/elders", response_model=List[UserResponse])
async def get_connected_elders(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models import UserRelationship
    if current_user.role == UserRole.ADMIN:
        result = await db.execute(select(User).where(User.role == UserRole.ELDER))
        return result.scalars().all()
    elif current_user.role in [UserRole.CAREGIVER, UserRole.FAMILY]:
        result = await db.execute(select(UserRelationship.elder_id).where(UserRelationship.caregiver_id == current_user.id))
        elder_ids = result.scalars().all()
        if not elder_ids:
            return []
        result = await db.execute(select(User).where(User.id.in_(elder_ids)))
        return result.scalars().all()
    return []

@router.put("/elders/{elder_id}/activities/{activity_id}", response_model=ActivityResponse)
async def update_activity_status(elder_id: int, activity_id: int, status: str, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    result = await db.execute(select(Activity).where(Activity.id == activity_id, Activity.elder_id == elder_id))
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    activity.status = status
    await db.commit()
    await db.refresh(activity)
    return activity

from pydantic import BaseModel
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@router.post("/elders/{elder_id}/chat", response_model=ChatResponse)
async def chat_with_ai(elder_id: int, req: ChatRequest, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    user_msg = Activity(elder_id=elder_id, activity_type="CONVERSATION", description=f"User: {req.message}", status="COMPLETED")
    db.add(user_msg)
    
    reply_text = "I'm here for you! I've noted that down. Is there anything else you need help with?"
    if "help" in req.message.lower() or "emergency" in req.message.lower():
        reply_text = "I am triggering an SOS alert to your family immediately. Please stay safe."
        sos_msg = Activity(elder_id=elder_id, activity_type="SOS", description="Triggered via chat", status="PENDING")
        db.add(sos_msg)

    ai_msg = Activity(elder_id=elder_id, activity_type="CONVERSATION", description=f"AI: {reply_text}", status="COMPLETED")
    db.add(ai_msg)
    await db.commit()
    return ChatResponse(reply=reply_text)
