from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from app.db.database import Base
from datetime import datetime, timezone
import enum

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
