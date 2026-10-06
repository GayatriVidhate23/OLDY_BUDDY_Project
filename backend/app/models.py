from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, JSON, DateTime
from app.database import Base
from datetime import datetime, timezone
import enum

class UserRole(str, enum.Enum):
    ELDER = "ELDER"
    CAREGIVER = "CAREGIVER"
    FAMILY = "FAMILY"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.ELDER, nullable=False)
    is_active = Column(Boolean, default=True)

class ElderProfile(Base):
    __tablename__ = "elder_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    name = Column(String, nullable=True)
    preferred_name = Column(String, nullable=True)
    phone_e164 = Column(String, nullable=True)
    language_code = Column(String, default="en-IN")
    tts_speaker = Column(String, nullable=True)
    timezone = Column(String, default="Asia/Kolkata")
    quiet_hours = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    last_interaction_at = Column(DateTime, nullable=True)
    last_checkin_at = Column(DateTime, nullable=True)

class RelationshipType(str, enum.Enum):
    CAREGIVER = "CAREGIVER"
    FAMILY = "FAMILY"

class UserRelationship(Base):
    __tablename__ = "user_relationships"
    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, ForeignKey("users.id"), index=True)
    caregiver_id = Column(Integer, ForeignKey("users.id"), index=True)
    type = Column(Enum(RelationshipType), nullable=False)

class ActivityType(str, enum.Enum):
    REMINDER = "REMINDER"
    CHECK_IN = "CHECK_IN"
    SOS = "SOS"

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, ForeignKey("users.id"))
    activity_type = Column(String, nullable=False)
    description = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String, default="PENDING")

class CallRecord(Base):
    __tablename__ = "call_records"
    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, ForeignKey("users.id"))
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


class ElderRoutine(Base):
    __tablename__ = "elder_routines"
    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True)
    wake_time = Column(String)
    sleep_time = Column(String)
    meal_times = Column(JSON, default=list)
    checkin_times = Column(JSON, default=list)

class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"
    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, ForeignKey("users.id"), index=True)
    name = Column(String, nullable=False)
    phone_e164 = Column(String, nullable=False)
    priority = Column(Integer, nullable=False)

class ElderConsent(Base):
    __tablename__ = "elder_consents"
    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, ForeignKey("users.id"), index=True)
    kind = Column(String, nullable=False)
    version = Column(String)
    evidence = Column(String)
    revoked_at = Column(DateTime, nullable=True)

class ElderPairingCode(Base):
    __tablename__ = "elder_pairing_codes"
    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, ForeignKey("users.id"), index=True)
    code = Column(String, nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)



class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    event_type = Column(String, index=True, nullable=False)
    source = Column(String, nullable=True)
    payload = Column(JSON, default=dict)
    occurred_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    severity = Column(String, nullable=False)
    title = Column(String, nullable=False)
    details = Column(String, nullable=True)
    source_event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    status = Column(String, default="open", index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution = Column(String, nullable=True)
    escalation_stage = Column(Integer, default=0)
    next_escalation_time = Column(DateTime, nullable=True)

class NotificationJob(Base):
    __tablename__ = "notification_jobs"
    id = Column(Integer, primary_key=True, index=True)
    type_channel = Column(String, nullable=False)
    recipient = Column(String, nullable=False)
    elder_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True)
    payload = Column(JSON, default=dict)
    status = Column(String, default="pending", index=True)
    attempt_count = Column(Integer, default=0)
    next_attempt_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    error = Column(String, nullable=True)
