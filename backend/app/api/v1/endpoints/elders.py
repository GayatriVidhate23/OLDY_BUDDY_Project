from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api import deps
from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.elder_profile import ElderProfile
from app.schemas.elder import ElderProfileResponse, ElderProfileCreate

router = APIRouter()

@router.get("/{elder_id}/profile", response_model=ElderProfileResponse)
async def get_elder_profile(
    elder_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    await deps.verify_elder_access(elder_id, current_user, db)
    result = await db.execute(select(ElderProfile).where(ElderProfile.user_id == elder_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.post("/{elder_id}/profile", response_model=ElderProfileResponse)
async def create_elder_profile(
    elder_id: int,
    profile_in: ElderProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    await deps.verify_elder_access(elder_id, current_user, db)
    profile = ElderProfile(**profile_in.model_dump())
    profile.user_id = elder_id
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile
