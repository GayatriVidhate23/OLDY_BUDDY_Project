from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models import UserRole, ActivityType, RelationshipType

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.ELDER

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    type: Optional[str] = "access"

# --- Elder Profile Schemas ---
class ElderProfileBase(BaseModel):
    preferences: Optional[Dict[str, Any]] = {}
    medical_info: Optional[Dict[str, Any]] = {}
    routines: Optional[Dict[str, Any]] = {}
    emergency_contact: Optional[str] = None

class ElderProfileCreate(ElderProfileBase):
    user_id: int

class ElderProfileUpdate(ElderProfileBase):
    pass

class ElderProfileResponse(ElderProfileBase):
    id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)

# --- Activity Schemas ---
class ActivityBase(BaseModel):
    activity_type: str
    description: Optional[str] = None
    status: Optional[str] = "PENDING"

class ActivityCreate(ActivityBase):
    pass

class ActivityUpdate(BaseModel):
    status: str

class ActivityResponse(ActivityBase):
    id: int
    elder_id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Relationship Schemas ---
class RelationshipCreate(BaseModel):
    elder_id: int
    caregiver_id: int
    type: RelationshipType

class RelationshipResponse(BaseModel):
    id: int
    elder_id: int
    caregiver_id: int
    type: RelationshipType
    model_config = ConfigDict(from_attributes=True)

# --- Voice Agent Schemas ---
class VoiceCallCreate(BaseModel):
    elder_id: int
    call_type: Optional[str] = "OUTBOUND_CHECKIN"
    phone_number: Optional[str] = None

class VoiceCallResponse(BaseModel):
    id: int
    elder_id: int
    phone_number: Optional[str] = None
    call_type: str
    status: str
    duration_seconds: int
    transcript: Optional[str] = None
    ai_summary: Optional[str] = None
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class VoiceWebhookRequest(BaseModel):
    call_id: Optional[int] = None
    elder_id: int
    user_speech: str

class VoiceWebhookResponse(BaseModel):
    twiml_response: str
    ai_reply: str
    action_taken: Optional[str] = None

# --- Alert Schemas ---
class AlertResponse(BaseModel):
    id: int
    elder_id: int
    severity: str
    message: str
    is_resolved: bool
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Dashboard Overview Schema ---
class DashboardOverviewResponse(BaseModel):
    elder_id: int
    elder_name: str
    elder_email: str
    emergency_contact: Optional[str] = None
    last_check_in: Optional[datetime] = None
    last_interaction: Optional[datetime] = None
    status_badge: str # "CHECKED_IN", "PENDING_CHECKIN", "SOS_ALERT", "ATTENTION_REQUIRED"
    active_alerts_count: int
    today_reminders_count: int
    completed_reminders_count: int
    missed_reminders_count: int

# --- AI Conversation Schemas ---
class ConversationRequest(BaseModel):
    prompt: str
    elder_id: Optional[int] = None

class ConversationResponse(BaseModel):
    reply: str
    timestamp: datetime

# --- Health Check Schema ---
class HealthResponse(BaseModel):
    status: str
    service: str
