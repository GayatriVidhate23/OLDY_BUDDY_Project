from typing import List, Optional, Union
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
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
    
    code = "123456"  # Mock OTP
    expires = datetime.now(timezone.utc) + timedelta(minutes=5)
    otp = OTP(user_id=user.id, code=get_password_hash(code), expires_at=expires)
    db.add(otp)
    await db.commit()
    return {"msg": "OTP generated. (Mock: 123456)"}

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
