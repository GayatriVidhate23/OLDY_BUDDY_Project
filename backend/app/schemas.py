from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models import UserRole
import re

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.ELDER

class UserCreate(UserBase):
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        return v

class UserResponse(UserBase):
    id: int
    is_active: bool

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class OTPRequest(BaseModel):
    email: EmailStr

class OTPVerify(BaseModel):
    email: EmailStr
    code: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None

class ElderProfileBase(BaseModel):
    name: Optional[str] = None
    preferred_name: Optional[str] = None
    phone_e164: Optional[str] = None
    language_code: Optional[str] = "en-IN"
    tts_speaker: Optional[str] = None
    timezone: Optional[str] = "Asia/Kolkata"
    quiet_hours: Optional[str] = None
    is_active: Optional[bool] = True
    last_interaction_at: Optional[datetime] = None
    last_checkin_at: Optional[datetime] = None

    @field_validator('phone_e164')
    @classmethod
    def validate_phone(cls, v):
        if v and not re.match(r"^\+[1-9]\d{1,14}$", v):
            raise ValueError("Phone number must be in E.164 format")
        return v
        
    @field_validator('language_code')
    @classmethod
    def validate_lang(cls, v):
        allowed = ["en-IN", "hi-IN", "bn-IN", "ta-IN", "te-IN", "gu-IN", "kn-IN", "ml-IN", "mr-IN", "pa-IN", "od-IN"]
        if v and v not in allowed:
            raise ValueError(f"Language code {v} not in allowed list")
        return v
        
    @field_validator('tts_speaker')
    @classmethod
    def validate_speaker(cls, v):
        allowed = ["speaker_1", "speaker_2", "female_en_in"]
        if v and v not in allowed:
            raise ValueError(f"TTS speaker {v} not allowed")
        return v

class ElderProfileResponse(ElderProfileBase):
    id: int
    user_id: int

class ElderRoutineBase(BaseModel):
    wake_time: str
    sleep_time: str
    meal_times: list[str] = []
    checkin_times: list[str] = []

    @field_validator('sleep_time')
    @classmethod
    def validate_times(cls, v, info):
        if 'wake_time' in info.data and v == info.data['wake_time']:
            raise ValueError("wake_time and sleep_time cannot be the same")
        return v

    @field_validator('checkin_times')
    @classmethod
    def validate_checkins(cls, v):
        if len(v) != len(set(v)):
            raise ValueError("checkin_times must be unique")
        return sorted(v)

class EmergencyContactBase(BaseModel):
    name: str
    phone_e164: str

    @field_validator('phone_e164')
    @classmethod
    def validate_phone(cls, v):
        if v and not re.match(r"^\+[1-9]\d{1,14}$", v):
            raise ValueError("Phone number must be in E.164 format")
        return v

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

class ActivityBase(BaseModel):
    activity_type: str
    description: Optional[str] = None
    status: Optional[str] = "PENDING"

class ActivityResponse(ActivityBase):
    id: int
    elder_id: int
    timestamp: datetime

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

class SOSResponse(BaseModel):
    alert_id: Optional[int] = None
    msg: str

class VerifySOS(BaseModel):
    safe: bool

class AlertResponse(BaseModel):
    id: int
    elder_id: int
    severity: str
    title: str
    status: str
    created_at: datetime
    resolution: Optional[str] = None
    
class EventResponse(BaseModel):
    id: int
    event_type: str
    occurred_at: datetime
    payload: dict

from typing import Dict, Any

class DashboardOverviewResponse(BaseModel):
    elder_id: int
    elder_name: str
    elder_email: str
    emergency_contact: Optional[str] = None
    last_check_in: Optional[datetime] = None
    last_interaction: Optional[datetime] = None
    status_badge: str
    active_alerts_count: int
    today_reminders_count: int
    completed_reminders_count: int
    missed_reminders_count: int

class ConversationRequest(BaseModel):
    prompt: str
    elder_id: Optional[int] = None

class ConversationResponse(BaseModel):
    reply: str
    timestamp: datetime

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

class HealthResponse(BaseModel):
    status: str
    service: str



class ElderProfileCreate(BaseModel):
    pass

ElderProfileUpdate = ElderProfileBase
ElderProfileCreate = ElderProfileBase


class RelationshipCreate(BaseModel): pass
class RelationshipResponse(BaseModel): pass






class RelationshipResponse(BaseModel): pass
class VoiceCallCreate(BaseModel):
    elder_id: int
    call_type: str
    phone_number: Optional[str] = None
    status: str = "PENDING"


class VoiceWebhookResponse(BaseModel): pass

class CallRecordResponse(BaseModel):
    id: int = 1

class OutboundCallRequest(BaseModel):
    elder_id: int
    call_type: str

class VoiceWebhookRequest(BaseModel):
    user_speech: str = ""
    call_id: str = ""
    event_type: str = ""

class VoiceCallResponse(BaseModel):
    id: int = 1
    elder_id: int = 1
    status: str = "COMPLETED"

class AlertResponse(BaseModel):
    id: int = 1
    elder_id: int = 1
    alert_type: str = "SOS"
    status: str = "PENDING"
    title: str = "Alert"
    message: str = "Alert message"

class ActivityCreate(BaseModel):
    activity_type: str
    description: str

# --- Module 8 Schemas ---
class ElderStatusResponse(BaseModel):
    status: str
    headline: str

class TrendDay(BaseModel):
    date: str
    reminders_completed: int
    reminders_missed: int
    checkins_completed: int
    checkins_missed: int
    conversations: int

class TrendsResponse(BaseModel):
    days: List[TrendDay]

class MessageCreate(BaseModel):
    body: str
    kind: Optional[str] = "text"

class MessageResponse(BaseModel):
    id: int
    elder_id: int
    sender_user_id: int
    sender_role: str
    kind: str
    body: str
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- Module 4 Schemas ---
class ReminderCreate(BaseModel):
    title: str
    kind: str
    recurrence: str
    times: List[str] = []
    dates: List[str] = []
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    max_attempts: Optional[int] = 3
    retry_minutes: Optional[int] = 15

class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    kind: Optional[str] = None
    recurrence: Optional[str] = None
    times: Optional[List[str]] = None
    dates: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    max_attempts: Optional[int] = None
    retry_minutes: Optional[int] = None
    is_active: Optional[bool] = None

class ReminderResponse(BaseModel):
    id: int
    elder_id: int
    title: str
    kind: str
    recurrence: str
    times: List[str]
    dates: List[str]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    max_attempts: int
    retry_minutes: int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class OccurrenceResponse(BaseModel):
    id: int
    reminder_id: int
    due_at: datetime
    status: str
    attempt_count: int
    last_attempt_at: Optional[datetime] = None
    next_attempt_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

