import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, JSON, DateTime, Text
from app.database import Base

class UserRole(str, enum.Enum):
    ELDER = "ELDER"
    CAREGIVER = "CAREGIVER"
    FAMILY = "FAMILY"
    ADMIN = "ADMIN"

class ActivityType(str, enum.Enum):
    REMINDER = "REMINDER"
    CHECK_IN = "CHECK_IN"
    SOS = "SOS"
    ALERT = "ALERT"
    EVENT = "EVENT"
    CONVERSATION = "CONVERSATION"

class RelationshipType(str, enum.Enum):
    CAREGIVER = "CAREGIVER"
    FAMILY = "FAMILY"

class NotificationChannel(str, enum.Enum):
    PUSH = "PUSH"
    SMS = "SMS"
    CALL = "CALL"

class NotificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.ELDER, nullable=False)
    is_active = Column(Boolean, default=True)

class ElderProfile(Base):
    __tablename__ = "elder_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    preferences = Column(JSON, default={})
    medical_info = Column(JSON, default={})
    routines = Column(JSON, default={})
    emergency_contact = Column(String, nullable=True)

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    activity_type = Column(String, nullable=False)
    description = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String, default="PENDING")

class UserRelationship(Base):
    __tablename__ = "user_relationships"
    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    caregiver_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    type = Column(Enum(RelationshipType), nullable=False)

class VoiceCall(Base):
    __tablename__ = "voice_calls"
    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    phone_number = Column(String, nullable=True)
    call_type = Column(String, default="OUTBOUND_CHECKIN") # OUTBOUND_CHECKIN, OUTBOUND_REMINDER, INBOUND
    status = Column(String, default="COMPLETED") # COMPLETED, MISSED, FAILED, IN_PROGRESS
    duration_seconds = Column(Integer, default=30)
    transcript = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class AlertNotification(Base):
    __tablename__ = "alert_notifications"
    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    severity = Column(String, default="HIGH") # INFO, WARNING, EMERGENCY, HIGH, MEDIUM, LOW
    message = Column(String, nullable=False)
    is_resolved = Column(Boolean, default=False)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    escalation_stage = Column(Integer, default=1)
    escalation_status = Column(String, default="ACTIVE") # ACTIVE, ACKNOWLEDGED, ESCALATED, COMPLETED
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alert_notifications.id"), index=True, nullable=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    channel = Column(String, nullable=False) # PUSH, SMS, CALL
    status = Column(String, default="PENDING", nullable=False) # PENDING, PROCESSING, SENT, FAILED, SKIPPED
    attempt_count = Column(Integer, default=0, nullable=False)
    next_attempt_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    provider_message_id = Column(String, nullable=True)
    last_error = Column(Text, nullable=True)
    payload = Column(JSON, default={})
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

class UserDevice(Base):
    __tablename__ = "user_devices"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    push_token = Column(String, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    device_type = Column(String, default="android", nullable=False) # android, ios
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

class CallRecord(Base):
    __tablename__ = "call_records"
    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, ForeignKey("users.id"), index=True)
    call_type = Column(String) # CHECK_IN, REMINDER
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime, nullable=True)
    outcome = Column(String, nullable=True) # COMPLETED, FAILED
    response = Column(String, nullable=True) # YES, NO, NEED_HELP
    status = Column(String, default="INITIATED")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)

class OTP(Base):
    __tablename__ = "otps"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    code = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    used = Column(Boolean, default=False)
