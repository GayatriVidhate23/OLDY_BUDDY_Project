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

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
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
    severity = Column(String, default="HIGH") # HIGH, MEDIUM, LOW
    message = Column(String, nullable=False)
    is_resolved = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
