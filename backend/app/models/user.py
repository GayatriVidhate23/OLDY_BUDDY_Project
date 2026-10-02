from sqlalchemy import Column, Integer, String, Boolean, Enum
from app.db.database import Base
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
