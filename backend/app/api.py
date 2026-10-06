from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, ActivityType
from app.schemas import (
    UserCreate,
    UserResponse,
    LoginRequest,
    Token,
    RefreshTokenRequest,
    ElderProfileResponse,
    ElderProfileUpdate,
    ActivityCreate,
    ActivityResponse,
    ActivityUpdate,
    RelationshipCreate,
    RelationshipResponse,
    VoiceCallCreate,
    VoiceCallResponse,
    VoiceWebhookRequest,
    VoiceWebhookResponse,
    AlertResponse,
    DashboardOverviewResponse,
    ConversationRequest,
    ConversationResponse,
    HealthResponse,
)
from app.auth import (
    get_current_active_user,
    verify_elder_access,
)
import app.services as services

api_router = APIRouter()

# --- Health Endpoint ---
@api_router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(status="ok", service="Oldy Buddy API")

# --- Authentication Endpoints ---
@api_router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    return await services.register_user(db, user_in)

@api_router.post("/auth/login", response_model=Token, tags=["Auth"])
async def login(login_req: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await services.authenticate_user(db, login_req.email, login_req.password)

@api_router.post("/auth/login/form", response_model=Token, tags=["Auth"])
async def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    return await services.authenticate_user(db, form_data.username, form_data.password)

@api_router.post("/auth/refresh", response_model=Token, tags=["Auth"])
async def refresh_token(req: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    return await services.refresh_access_token(db, req.refresh_token)

# --- User & Profile Endpoints ---
@api_router.get("/users/me", response_model=UserResponse, tags=["Users"])
async def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@api_router.get("/elders/{elder_id}", response_model=ElderProfileResponse, tags=["Elder Profiles"])
async def get_elder(
    elder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await verify_elder_access(elder_id, current_user, db)
    return await services.get_elder_profile(db, elder_id)

@api_router.put("/elders/{elder_id}", response_model=ElderProfileResponse, tags=["Elder Profiles"])
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

@api_router.post("/voice/webhook", response_model=VoiceWebhookResponse, tags=["Voice Agent"])
async def voice_webhook(
    req: VoiceWebhookRequest,
    db: AsyncSession = Depends(get_db),
):
    return await services.process_voice_webhook(db, req)

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
