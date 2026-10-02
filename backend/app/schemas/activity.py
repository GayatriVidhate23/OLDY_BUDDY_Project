from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ActivityBase(BaseModel):
    activity_type: str
    description: Optional[str] = None
    status: Optional[str] = "PENDING"

class ActivityCreate(ActivityBase):
    pass

class ActivityResponse(ActivityBase):
    id: int
    elder_id: int
    timestamp: datetime

    class Config:
        from_attributes = True
