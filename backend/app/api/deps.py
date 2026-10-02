from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.relationship import UserRelationship
from app.schemas.user import TokenPayload
from sqlalchemy import select

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    result = await db.execute(select(User).where(User.id == int(token_data.sub)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(roles: list[UserRole]):
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Not enough privileges")
        return current_user
    return role_checker

async def verify_elder_access(elder_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    if current_user.role == UserRole.ADMIN:
        return True
    if current_user.role == UserRole.ELDER and current_user.id == elder_id:
        return True
    
    # Check relationship
    result = await db.execute(select(UserRelationship).where(
        UserRelationship.elder_id == elder_id,
        UserRelationship.caregiver_id == current_user.id
    ))
    rel = result.scalar_one_or_none()
    if not rel:
        raise HTTPException(status_code=403, detail="Not authorized to access this elder's data")
    return True
