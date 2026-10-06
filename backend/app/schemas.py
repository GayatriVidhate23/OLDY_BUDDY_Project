from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, Dict, Any
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
    preferences: Optional[Dict[str, Any]] = {}
    medical_info: Optional[Dict[str, Any]] = {}
    emergency_contact: Optional[str] = None

class ElderProfileResponse(ElderProfileBase):
    id: int
    user_id: int

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
