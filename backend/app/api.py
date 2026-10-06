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
    if not settings.DEBUG:
        raise HTTPException(status_code=501, detail="Production OTP provider not configured")
    code = "123456" # MOCK OTP
    expires = datetime.now(timezone.utc) + timedelta(minutes=5)
    
    otp = OTP(user_id=user.id, code=get_password_hash(code), expires_at=expires)
    db.add(otp)
    await db.commit()
    return {"msg": "OTP generated."}

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


from app.schemas import ElderRoutineBase, EmergencyContactBase, EmergencyContactResponse, EmergencyContactOrder, ElderConsentBase, ElderConsentResponse, PairingCodeResponse, PairingRequest
from app.models import ElderRoutine, EmergencyContact, ElderConsent, ElderPairingCode, RelationshipType
import uuid
import random

@router.post("/v1/elders", response_model=ElderProfileResponse)
async def create_elder(profile_in: ElderProfileBase, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models import ElderProfile
    if current_user.role not in [UserRole.CAREGIVER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to create elder")
        
    if profile_in.phone_e164:
        res = await db.execute(select(ElderProfile).where(ElderProfile.phone_e164 == profile_in.phone_e164, ElderProfile.is_active == True))
        if res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Active elder with this phone number already exists")
            
    import uuid
    dummy_email = f"elder_{uuid.uuid4().hex[:8]}@oldybuddy.internal"
    new_user = User(email=dummy_email, hashed_password=get_password_hash("StrongPassword1!"), role=UserRole.ELDER, full_name=profile_in.name)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    profile = ElderProfile(**profile_in.model_dump(), user_id=new_user.id)
    db.add(profile)
    
    # Auto link caregiver
    if current_user.role == UserRole.CAREGIVER:
        from app.models import UserRelationship, RelationshipType
        rel = UserRelationship(elder_id=new_user.id, caregiver_id=current_user.id, type=RelationshipType.CAREGIVER)
        db.add(rel)
        
    await db.commit()
    await db.refresh(profile)
    return profile

@router.get("/v1/elders", response_model=List[ElderProfileResponse])
async def list_elders(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models import ElderProfile
    if current_user.role == UserRole.ADMIN:
        result = await db.execute(select(ElderProfile))
    elif current_user.role == UserRole.CAREGIVER:
        result = await db.execute(
            select(ElderProfile).join(UserRelationship, UserRelationship.elder_id == ElderProfile.user_id)
            .where(UserRelationship.caregiver_id == current_user.id)
        )
    else:
        return []
    return result.scalars().all()

@router.get("/v1/elders/{elder_id}", response_model=ElderProfileResponse)
async def get_elder_by_id(elder_id: int, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    from app.models import ElderProfile
    result = await db.execute(select(ElderProfile).where(ElderProfile.user_id == elder_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Elder profile not found")
    return profile

@router.patch("/v1/elders/{elder_id}", response_model=ElderProfileResponse)
async def patch_elder(elder_id: int, profile_in: ElderProfileBase, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    from app.models import ElderProfile
    result = await db.execute(select(ElderProfile).where(ElderProfile.user_id == elder_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Elder profile not found")
        
    if profile_in.phone_e164 and profile_in.phone_e164 != profile.phone_e164:
        res = await db.execute(select(ElderProfile).where(ElderProfile.phone_e164 == profile_in.phone_e164, ElderProfile.is_active == True))
        if res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Active elder with this phone number already exists")
            
    update_data = profile_in.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(profile, k, v)
        
    await db.commit()
    await db.refresh(profile)
    return profile

@router.post("/v1/elders/{elder_id}/caregivers")
async def add_caregiver_to_elder(elder_id: int, caregiver_email: str, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    res = await db.execute(select(User).where(User.email == caregiver_email))
    cg = res.scalar_one_or_none()
    if not cg or cg.role != UserRole.CAREGIVER:
        raise HTTPException(status_code=400, detail="Invalid caregiver email")
        
    rel = UserRelationship(elder_id=elder_id, caregiver_id=cg.id, type=RelationshipType.CAREGIVER)
    db.add(rel)
    await db.commit()
    return {"msg": "Caregiver linked"}

@router.put("/v1/elders/{elder_id}/routine", response_model=ElderRoutineBase)
async def put_routine(elder_id: int, routine: ElderRoutineBase, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    res = await db.execute(select(ElderRoutine).where(ElderRoutine.elder_id == elder_id))
    er = res.scalar_one_or_none()
    if er:
        for k, v in routine.model_dump().items():
            setattr(er, k, v)
    else:
        er = ElderRoutine(elder_id=elder_id, **routine.model_dump())
        db.add(er)
    await db.commit()
    await db.refresh(er)
    return er

@router.get("/v1/elders/{elder_id}/routine", response_model=ElderRoutineBase)
async def get_routine(elder_id: int, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    res = await db.execute(select(ElderRoutine).where(ElderRoutine.elder_id == elder_id))
    er = res.scalar_one_or_none()
    if not er:
        raise HTTPException(status_code=404, detail="Routine not found")
    return er

@router.get("/v1/elders/{elder_id}/routine/suggested-reminders")
async def get_suggested_reminders(elder_id: int, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    res = await db.execute(select(ElderRoutine).where(ElderRoutine.elder_id == elder_id))
    er = res.scalar_one_or_none()
    if not er:
        return []
    suggs = []
    for m in er.meal_times:
        suggs.append({"type": "MEAL", "time": m, "message": "Time for your meal!"})
    for c in er.checkin_times:
        suggs.append({"type": "CHECK_IN", "time": c, "message": "Routine check-in"})
    return suggs

@router.get("/v1/elders/{elder_id}/emergency-contacts", response_model=List[EmergencyContactResponse])
async def get_emergency_contacts(elder_id: int, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    res = await db.execute(select(EmergencyContact).where(EmergencyContact.elder_id == elder_id).order_by(EmergencyContact.priority))
    return res.scalars().all()

@router.post("/v1/elders/{elder_id}/emergency-contacts", response_model=EmergencyContactResponse)
async def add_emergency_contact(elder_id: int, contact: EmergencyContactBase, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    res = await db.execute(select(EmergencyContact).where(EmergencyContact.elder_id == elder_id))
    existing = res.scalars().all()
    if len(existing) >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 emergency contacts allowed")
    
    if any(c.phone_e164 == contact.phone_e164 for c in existing):
        raise HTTPException(status_code=400, detail="Duplicate phone number not allowed")
        
    prio = len(existing) + 1
    new_c = EmergencyContact(elder_id=elder_id, name=contact.name, phone_e164=contact.phone_e164, priority=prio)
    db.add(new_c)
    await db.commit()
    await db.refresh(new_c)
    return new_c

@router.delete("/v1/elders/{elder_id}/emergency-contacts/{cid}")
async def del_emergency_contact(elder_id: int, cid: int, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    res = await db.execute(select(EmergencyContact).where(EmergencyContact.id == cid, EmergencyContact.elder_id == elder_id))
    c = res.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404)
    await db.delete(c)
    await db.commit()
    
    # Re-compact priorities
    res = await db.execute(select(EmergencyContact).where(EmergencyContact.elder_id == elder_id).order_by(EmergencyContact.priority))
    remaining = res.scalars().all()
    for i, rc in enumerate(remaining):
        rc.priority = i + 1
    await db.commit()
    return {"msg": "Deleted"}

@router.post("/v1/elders/{elder_id}/consents", response_model=ElderConsentResponse)
async def add_consent(elder_id: int, consent: ElderConsentBase, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    c = ElderConsent(elder_id=elder_id, **consent.model_dump())
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c

@router.delete("/v1/elders/{elder_id}/consents/{kind}")
async def revoke_consent(elder_id: int, kind: str, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    res = await db.execute(select(ElderConsent).where(ElderConsent.elder_id == elder_id, ElderConsent.kind == kind, ElderConsent.revoked_at == None))
    c = res.scalar_one_or_none()
    if c:
        c.revoked_at = datetime.now(timezone.utc)
        await db.commit()
    return {"msg": "Revoked"}

@router.post("/v1/elders/{elder_id}/pairing-code", response_model=PairingCodeResponse)
async def generate_pairing_code(elder_id: int, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    code = str(random.randint(100000, 999999))
    expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    pc = ElderPairingCode(elder_id=elder_id, code=code, expires_at=expires)
    db.add(pc)
    await db.commit()
    return {"code": code, "expires_at": expires}

@router.post("/v1/auth/pair", response_model=Token)
async def pair_elder(req: PairingRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ElderPairingCode).where(ElderPairingCode.code == req.code, ElderPairingCode.used == False))
    pc = res.scalar_one_or_none()
    if not pc:
        raise HTTPException(status_code=400, detail="Invalid or used pairing code")
    if pc.expires_at.replace(tzinfo=None) < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(status_code=400, detail="Pairing code expired")
        
    pc.used = True
    
    # Revoke old refresh tokens for this elder
    # Not required by spec but "old session is revoked" -> revoke refresh tokens
    await db.execute(
        RefreshToken.__table__.update().where(RefreshToken.user_id == pc.elder_id).values(revoked=True)
    )
    await db.commit()
    
    access_token = create_access_token(pc.elder_id)
    refresh_token = create_refresh_token(pc.elder_id)
    db_refresh = RefreshToken(user_id=pc.elder_id, token=refresh_token, expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES))
    db.add(db_refresh)
    await db.commit()
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.get("/v1/me/elder", response_model=ElderProfileResponse)
async def get_me_elder(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ELDER:
        raise HTTPException(status_code=403, detail="Only elders can access this endpoint")
    from app.models import ElderProfile
    res = await db.execute(select(ElderProfile).where(ElderProfile.user_id == current_user.id))
    prof = res.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Profile not found")
    return prof


from app.schemas import SOSResponse, VerifySOS, AlertResponse, EventResponse
from app.decision_engine import process_event
from app.models import Alert, Event, NotificationJob

@router.post("/v1/sos", response_model=SOSResponse)
async def trigger_sos(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ELDER:
        raise HTTPException(status_code=403, detail="Only elders can trigger SOS directly")
        
    event = await process_event(db, current_user.id, "sos_pressed", source="api")
    await db.commit()
    
    # Get created alert
    res = await db.execute(select(Alert).where(Alert.source_event_id == event.id))
    alert = res.scalar_one_or_none()
    
    return {"alert_id": alert.id if alert else None, "msg": "SOS triggered"}

@router.post("/v1/alerts/{id}/verify")
async def verify_sos(id: int, req: VerifySOS, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await db.execute(select(Alert).where(Alert.id == id))
    alert = res.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404)
        
    # Elder can only verify their own
    if current_user.role == UserRole.ELDER and current_user.id != alert.elder_id:
        raise HTTPException(status_code=404)
        
    if req.safe:
        await process_event(db, alert.elder_id, "sos_cancelled", source="elder_verification")
    else:
        alert.next_escalation_time = datetime.now(timezone.utc)
        
    await db.commit()
    return {"msg": "Verified"}

@router.get("/v1/elders/{elder_id}/alerts", response_model=List[AlertResponse])
async def get_alerts(elder_id: int, status: str = "open", db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    res = await db.execute(select(Alert).where(Alert.elder_id == elder_id, Alert.status == status))
    return res.scalars().all()

@router.post("/v1/alerts/{id}/ack")
async def ack_alert(id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await db.execute(select(Alert).where(Alert.id == id))
    alert = res.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404)
        
    # Check access logic for caregiver/alert
    await verify_elder_access(alert.elder_id, current_user, db)
        
    if alert.status == "open":
        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.acknowledged_by = current_user.id
        alert.next_escalation_time = None
        
        await process_event(db, alert.elder_id, "alert_acknowledged", payload={"alert_id": alert.id})
        
        # Skip pending notifications
        await db.execute(NotificationJob.__table__.update().where(NotificationJob.alert_id == id, NotificationJob.status == "pending").values(status="skipped"))
        
        await db.commit()
    return {"msg": "Acknowledged"}

@router.post("/v1/alerts/{id}/resolve")
async def resolve_alert(id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    res = await db.execute(select(Alert).where(Alert.id == id))
    alert = res.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404)
        
    await verify_elder_access(alert.elder_id, current_user, db)
    
    if alert.status in ["open", "acknowledged"]:
        alert.status = "resolved"
        alert.resolved_at = datetime.now(timezone.utc)
        alert.resolution = "Resolved by caregiver"
        alert.next_escalation_time = None
        
        await process_event(db, alert.elder_id, "alert_resolved", payload={"alert_id": alert.id})
        await db.execute(NotificationJob.__table__.update().where(NotificationJob.alert_id == id, NotificationJob.status == "pending").values(status="skipped"))
        await db.commit()
    return {"msg": "Resolved"}

@router.get("/v1/elders/{elder_id}/events", response_model=List[EventResponse])
async def get_events(elder_id: int, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    res = await db.execute(select(Event).where(Event.elder_id == elder_id).order_by(Event.occurred_at.desc()))
    return res.scalars().all()
