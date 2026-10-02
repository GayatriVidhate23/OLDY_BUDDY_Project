from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from app.db.database import Base

class ElderProfile(Base):
    __tablename__ = "elder_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    preferences = Column(JSON, default={})
    medical_info = Column(JSON, default={})
    emergency_contact = Column(String)
