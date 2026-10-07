from typing import List, Optional, Union
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError

from app.database import get_db, settings
from app.models import User, UserRole, Activity, ActivityType, RefreshToken, OTP, UserRelationship
from app.schemas import (
    UserCreate,
    UserResponse,
    LoginRequest,
    Token,
    RefreshTokenRequest,
    TokenRefreshRequest,
    OTPRequest,
    OTPVerify,
    ElderProfileResponse,
    ElderProfileUpdate,
    ElderProfileBase,
    ActivityCreate,
    ActivityBase,
    ActivityResponse,
    ActivityUpdate,
    RelationshipCreate,
    RelationshipResponse,
    VoiceCallCreate,
    VoiceCallResponse,
    VoiceWebhookRequest,
    VoiceWebhookResponse,
    OutboundCallRequest,
    WebhookPayload,
    CallRecordResponse,
    AlertResponse,
    DashboardOverviewResponse,
    ConversationRequest,
    ConversationResponse,
    HealthResponse,
    DeviceRegisterRequest,
    DeviceRegisterResponse,
    NotificationOutboxResponse,
    ChatRequest,
    ChatResponse,
)
from app.auth import (
    get_current_active_user,
    get_current_user,
    verify_elder_access,
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)
import app.services as services

api_router = APIRouter()
router = api_router  # Alias for compatibility

# --- Health Endpoint ---
@api_router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(status="ok", service="Oldy Buddy API")

# --- Authentication Endpoints ---
@api_router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    if user_in.role == UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Public registration of ADMIN is forbidden")
    return await services.register_user(db, user_in)

@api_router.post("/auth/login", response_model=Token, tags=["Auth"])
async def login(request: Request, db: AsyncSession = Depends(get_db)):
    content_type = request.headers.get("content-type", "")
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        email = form.get("username") or form.get("email")
        password = form.get("password")
    else:
        try:
            data = await request.json()
            email = data.get("email") or data.get("username")
            password = data.get("password")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid login payload")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Missing email or password")

    return await services.authenticate_user(db, str(email), str(password))

@api_router.post("/auth/login/form", response_model=Token, tags=["Auth"])
async def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    return await services.authenticate_user(db, form_data.username, form_data.password)

@api_router.post("/auth/refresh", response_model=Token, tags=["Auth"])
async def refresh_token(req: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    return await services.refresh_access_token(db, req.refresh_token)

@api_router.post("/auth/logout", tags=["Auth"])
async def logout(req: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == req.refresh_token))
    token = result.scalar_one_or_none()
    if token:
        token.revoked = True
        await db.commit()
    return {"msg": "Logged out successfully"}

@api_router.post("/auth/request-otp", tags=["Auth"])
async def request_otp(req: OTPRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user:
        return {"msg": "If email exists, OTP sent"}
    
    if not settings.DEBUG:
        raise HTTPException(status_code=501, detail="Production OTP provider not configured")
    code = "123456"  # MOCK OTP
    expires = datetime.now(timezone.utc) + timedelta(minutes=5)
    otp = OTP(user_id=user.id, code=get_password_hash(code), expires_at=expires)
    db.add(otp)
    await db.commit()
    return {"msg": "OTP generated."}

@api_router.post("/auth/verify-otp", response_model=Token, tags=["Auth"])
async def verify_otp(req: OTPVerify, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    result = await db.execute(select(OTP).where(OTP.user_id == user.id, OTP.used == False).order_by(OTP.id.desc()))
    otp = result.scalar_one_or_none()
    if not otp or otp.attempts >= 3:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
    if not verify_password(req.code, otp.code):
        otp.attempts += 1
        await db.commit()
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    otp.used = True
    await db.commit()
    
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

@api_router.get("/users/me", response_model=UserResponse, tags=["Users"])
@api_router.get("/auth/me", response_model=UserResponse, tags=["Auth"])
async def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# --- User & Profile Endpoints ---
@api_router.get("/elders/{elder_id}", response_model=ElderProfileResponse, tags=["Elder Profiles"])
@api_router.get("/elders/{elder_id}/profile", response_model=ElderProfileResponse, tags=["Elder Profiles"])
async def get_elder(
    elder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_elder_access(elder_id, current_user, db)
    return await services.get_elder_profile(db, elder_id)

@api_router.put("/elders/{elder_id}", response_model=ElderProfileResponse, tags=["Elder Profiles"])
@api_router.post("/elders/{elder_id}/profile", response_model=ElderProfileResponse, tags=["Elder Profiles"])
async def update_elder(
    elder_id: int,
    profile_in: ElderProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_elder_access(elder_id, current_user, db)
    return await services.update_elder_profile(db, elder_id, profile_in)

# --- Activity / Reminders / Check-ins / SOS Endpoints ---
@api_router.get("/elders/{elder_id}/activities", response_model=List[ActivityResponse], tags=["Activities"])
async def list_activities(
    elder_id: int,
    activity_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_elder_access(elder_id, current_user, db)
    return await services.get_activities_for_elder(db, elder_id, activity_type)

@api_router.post("/elders/{elder_id}/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED, tags=["Activities"])
async def create_activity(
    elder_id: int,
    activity_in: ActivityCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_elder_access(elder_id, current_user, db)
    return await services.create_activity(db, elder_id, activity_in)

@api_router.put("/activities/{activity_id}/status", response_model=ActivityResponse, tags=["Activities"])
async def update_activity_status(
    activity_id: int,
    status_in: ActivityUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await services.update_activity_status(db, activity_id, status_in.status)

@api_router.put("/elders/{elder_id}/activities/{activity_id}", response_model=ActivityResponse, tags=["Activities"])
async def update_elder_activity(
    elder_id: int,
    activity_id: int,
    status: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_elder_access(elder_id, current_user, db)
    return await services.update_activity_status(db, activity_id, status)

@api_router.post("/elders/{elder_id}/check-in", response_model=ActivityResponse, tags=["Activities"])
async def elder_check_in(
    elder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_elder_access(elder_id, current_user, db)
    act = ActivityCreate(activity_type=ActivityType.CHECK_IN.value, description="Daily Check-in completed", status="COMPLETED")
    return await services.create_activity(db, elder_id, act)

@api_router.post("/elders/{elder_id}/sos", response_model=ActivityResponse, tags=["Activities"])
async def elder_sos(
    elder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_elder_access(elder_id, current_user, db)
    act = ActivityCreate(activity_type=ActivityType.SOS.value, description="EMERGENCY SOS Triggered!", status="ALERT")
    return await services.create_activity(db, elder_id, act)

# --- Voice Agent Endpoints ---
@api_router.post("/voice/outbound-call", response_model=VoiceCallResponse, tags=["Voice Agent"])
async def make_outbound_call(
    call_in: VoiceCallCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_elder_access(call_in.elder_id, current_user, db)
    return await services.trigger_outbound_voice_call(db, call_in)

@api_router.post("/voice/outbound", response_model=CallRecordResponse, tags=["Voice Agent"])
async def make_outbound_call_record(req: OutboundCallRequest, db: AsyncSession = Depends(get_db)):
    return await services.initiate_call(db, req.elder_id, req.call_type)

@api_router.post("/voice/webhook", tags=["Voice Agent"])
async def voice_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    data = await request.json()
    if "user_speech" in data:
        req = VoiceWebhookRequest(**data)
        return await services.process_voice_webhook(db, req)
    elif "call_id" in data:
        call_id = data["call_id"]
        event_type = data.get("event_type")
        speech_text = data.get("speech_text")
        return await services.process_voice_webhook(db, call_id, event_type, speech_text)
    else:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

@api_router.get("/voice/history/{elder_id}", response_model=List[VoiceCallResponse], tags=["Voice Agent"])
async def get_call_history(
    elder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_elder_access(elder_id, current_user, db)
    return await services.get_voice_history(db, elder_id)

# --- Caregiver & Family Dashboard Endpoints ---
@api_router.get("/dashboard/overview/{elder_id}", response_model=DashboardOverviewResponse, tags=["Caregiver Dashboard"])
async def get_dashboard_summary(
    elder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_elder_access(elder_id, current_user, db)
    return await services.get_dashboard_overview(db, elder_id)

@api_router.get("/caregiver/elders", response_model=List[UserResponse], tags=["Caregiver Dashboard"])
async def get_connected_elders(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
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

@api_router.get("/alerts/{elder_id}", response_model=List[AlertResponse], tags=["Caregiver Dashboard"])
async def list_elder_alerts(
    elder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_elder_access(elder_id, current_user, db)
    return await services.get_elder_alerts(db, elder_id)

@api_router.put("/alerts/{alert_id}/resolve", response_model=AlertResponse, tags=["Caregiver Dashboard"])
async def resolve_elder_alert(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await services.resolve_alert(db, alert_id)

# --- Relationship Endpoints ---
@api_router.post("/relationships", response_model=RelationshipResponse, status_code=status.HTTP_201_CREATED, tags=["Relationships"])
async def add_relationship(
    rel_in: RelationshipCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await services.create_relationship(db, rel_in)

@api_router.get("/elders/{elder_id}/relationships", response_model=List[RelationshipResponse], tags=["Relationships"])
async def list_relationships(
    elder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_elder_access(elder_id, current_user, db)
    return await services.get_elder_relationships(db, elder_id)

# --- AI Conversation Endpoint ---
@api_router.post("/conversation", response_model=ConversationResponse, tags=["AI Conversation"])
async def conversation(
    req: ConversationRequest,
    current_user: User = Depends(get_current_active_user),
):
    return await services.process_ai_conversation(req)

# --- Notification & Device Endpoints ---
@api_router.post("/devices/register", response_model=DeviceRegisterResponse, tags=["Notifications"])
async def register_device(
    req: DeviceRegisterRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models import UserDevice
    res = await db.execute(
        select(UserDevice).where(
            UserDevice.user_id == current_user.id,
            UserDevice.push_token == req.push_token,
        )
    )
    device = res.scalar_one_or_none()
    if not device:
        device = UserDevice(
            user_id=current_user.id,
            push_token=req.push_token,
            is_active=True,
            device_type=req.device_type or "android",
        )
        db.add(device)
    else:
        device.is_active = True
        device.device_type = req.device_type or device.device_type

    await db.commit()
    await db.refresh(device)
    return device

@api_router.post("/alerts/{alert_id}/acknowledge", response_model=AlertResponse, tags=["Notifications"])
async def acknowledge_elder_alert(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.notify.policy import acknowledge_alert
    alert = await acknowledge_alert(db, alert_id, current_user.id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@api_router.get("/notifications/outbox", response_model=List[NotificationOutboxResponse], tags=["Notifications"])
async def get_notification_outbox(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models import Notification
    res = await db.execute(select(Notification).order_by(Notification.created_at.desc()).limit(100))
    return res.scalars().all()

@api_router.post("/notifications/dispatcher/run", tags=["Notifications"])
async def run_notification_dispatcher(
    db: AsyncSession = Depends(get_db),
):
    from app.services.notify.dispatcher import NotificationDispatcher
    dispatcher = NotificationDispatcher()
    processed = await dispatcher.process_outbox(db)
    return {"status": "ok", "processed_count": len(processed)}
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

# --- Voice Agent Endpoints ---
from app.services.voice.session import VoiceSession

@api_router.websocket("/v1/voice/ws")
async def voice_websocket(websocket: WebSocket, elder_id: int = None, db: AsyncSession = Depends(get_db)):
    session = VoiceSession(websocket, elder_id, db)
    await session.start()

# --- Module 8 Endpoints ---
from app.schemas import ElderStatusResponse, TrendsResponse, MessageCreate, MessageResponse
from app.services.module8 import get_elder_status, get_elder_trends, send_message, get_messages

@router.get("/v1/elders/{elder_id}/status", response_model=ElderStatusResponse)
async def api_get_status(elder_id: int, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    return await get_elder_status(db, elder_id)

@router.get("/v1/elders/{elder_id}/trends", response_model=TrendsResponse)
async def api_get_trends(elder_id: int, days: int = 7, db: AsyncSession = Depends(get_db), _: bool = Depends(verify_elder_access)):
    if days not in [7, 30]:
        raise HTTPException(status_code=400, detail="Days must be 7 or 30")
    return await get_elder_trends(db, elder_id, days)

@router.post("/v1/elders/{elder_id}/messages", response_model=MessageResponse)
async def api_post_message(elder_id: int, message: MessageCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user), _: bool = Depends(verify_elder_access)):
    if len(message.body) > 500:
        raise HTTPException(status_code=400, detail="Message body must be 500 characters or less")
    
    msg = await send_message(db, elder_id, current_user.id, current_user.role, message.body, message.kind)
    
    # Trigger push notification here if we had a push service
    # e.g., await enqueue_notification(...)
    
    return msg

@router.get("/v1/elders/{elder_id}/messages", response_model=List[MessageResponse])
async def api_get_messages(elder_id: int, cursor: int = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user), _: bool = Depends(verify_elder_access)):
    return await get_messages(db, elder_id, current_user.id, current_user.role, limit=50)
