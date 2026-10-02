from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.api import deps
from app.db.database import get_db
from app.models.user import User
from app.models.activity import Activity
from app.schemas.activity import ActivityCreate, ActivityResponse
from app.intelligence.workflow_engine import process_activity

router = APIRouter()

@router.post("/{elder_id}/activities", response_model=ActivityResponse)
async def create_activity(
    elder_id: int,
    activity_in: ActivityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    await deps.verify_elder_access(elder_id, current_user, db)
    activity = Activity(**activity_in.model_dump(), elder_id=elder_id)
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    
    # Trigger Intelligence Workflow
    await process_activity(activity, db)
    
    return activity

@router.get("/{elder_id}/activities", response_model=List[ActivityResponse])
async def list_activities(
    elder_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    await deps.verify_elder_access(elder_id, current_user, db)
    result = await db.execute(select(Activity).where(Activity.elder_id == elder_id))
    return result.scalars().all()
