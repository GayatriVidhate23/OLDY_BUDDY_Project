from pydantic import BaseModel
from typing import Dict, Any, Optional

class ElderProfileBase(BaseModel):
    preferences: Optional[Dict[str, Any]] = {}
    medical_info: Optional[Dict[str, Any]] = {}
    emergency_contact: Optional[str] = None

class ElderProfileCreate(ElderProfileBase):
    user_id: int

class ElderProfileResponse(ElderProfileBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
