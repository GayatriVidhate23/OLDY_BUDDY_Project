from sqlalchemy import Column, Integer, ForeignKey, Enum
from app.db.database import Base
import enum

class RelationshipType(str, enum.Enum):
    CAREGIVER = "CAREGIVER"
    FAMILY = "FAMILY"

class UserRelationship(Base):
    __tablename__ = "user_relationships"
    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, ForeignKey("users.id"), index=True)
    caregiver_id = Column(Integer, ForeignKey("users.id"), index=True)
    type = Column(Enum(RelationshipType), nullable=False)
