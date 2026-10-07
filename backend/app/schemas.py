import re
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
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

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 4:
            raise ValueError("Password must be at least 4 characters")
        return v

class UserResponse(UserBase):
    id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerify(BaseModel):
    email: EmailStr
    code: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    type: Optional[str] = "access"

# --- Elder Profile Schemas ---
class ElderProfileBase(BaseModel):
    preferences: Optional[Dict[str, Any]] = {}
    medical_info: Optional[Dict[str, Any]] = {}
    routines: Optional[Dict[str, Any]] = {}
    emergency_contact: Optional[str] = None
    name: Optional[str] = None
    preferred_name: Optional[str] = None
    phone_e164: Optional[str] = None
    language_code: Optional[str] = "en-IN"
    tts_speaker: Optional[str] = None
    timezone: Optional[str] = "Asia/Kolkata"

    @field_validator("language_code")
    @classmethod
    def validate_language_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ["en-IN", "hi-IN", "ta-IN", "te-IN", "kn-IN", "mr-IN", "bn-IN", "gu-IN", "en-US"]:
            raise ValueError("Unsupported language code")
        return v
    quiet_hours: Optional[str] = None
    is_active: Optional[bool] = True
    last_interaction_at: Optional[datetime] = None
    last_checkin_at: Optional[datetime] = None

class ElderProfileCreate(ElderProfileBase):
    user_id: int

class ElderProfileUpdate(ElderProfileBase):
    pass

class ElderProfileResponse(ElderProfileBase):
    id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)

class ElderRoutineBase(BaseModel):
    wake_time: str
    sleep_time: str
    meal_times: list[str] = []
    checkin_times: list[str] = []

class EmergencyContactBase(BaseModel):
    name: str
    phone_e164: str

class EmergencyContactResponse(EmergencyContactBase):
    id: int
    priority: int

class EmergencyContactOrder(BaseModel):
    contact_ids: list[int]

class ElderConsentBase(BaseModel):
    kind: str
    version: Optional[str] = None
    evidence: Optional[str] = None

class ElderConsentResponse(ElderConsentBase):
    id: int
    revoked_at: Optional[datetime] = None

class PairingCodeResponse(BaseModel):
    code: str
    expires_at: datetime

class PairingRequest(BaseModel):
    code: str

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

class OutboundCallRequest(BaseModel):
    call_type: str
    elder_id: int

class WebhookPayload(BaseModel):
    call_id: int
    event_type: str # started, answered, speech, completed, failed
    speech_text: Optional[str] = None
    
class CallRecordResponse(BaseModel):
    id: int
    elder_id: int
    call_type: str
    status: str
    model_config = ConfigDict(from_attributes=True)

class SOSResponse(BaseModel):
    alert_id: Optional[int] = None
    msg: str

class VerifySOS(BaseModel):
    safe: bool

# --- Alert Schemas ---
class AlertResponse(BaseModel):
    id: int
    elder_id: int
    severity: str
    message: Optional[str] = None
    title: Optional[str] = None
    status: Optional[str] = "open"
    is_resolved: Optional[bool] = False
    timestamp: Optional[datetime] = None
    created_at: Optional[datetime] = None
    resolution: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class EventResponse(BaseModel):
    id: int
    event_type: str
    occurred_at: datetime
    payload: dict
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

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

# --- Notification & Device Schemas ---
class DeviceRegisterRequest(BaseModel):
    push_token: str
    device_type: Optional[str] = "android"

class DeviceRegisterResponse(BaseModel):
    id: int
    user_id: int
    push_token: str
    is_active: bool
    device_type: str
    model_config = ConfigDict(from_attributes=True)

class NotificationOutboxResponse(BaseModel):
    id: int
    alert_id: Optional[int] = None
    recipient_id: int
    channel: str
    status: str
    attempt_count: int
    next_attempt_at: datetime
    provider_message_id: Optional[str] = None
    last_error: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Health Check Schema ---
class HealthResponse(BaseModel):
    status: str
    service: str
