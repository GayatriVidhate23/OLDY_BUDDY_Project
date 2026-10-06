from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import settings, get_db
from app.models import User, UserRole, UserRelationship, RefreshToken
from app.schemas import TokenPayload

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def create_access_token(subject: Union[str, Any]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"exp": expire, "sub": str(subject)}, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)

import uuid

def create_refresh_token(subject: Union[str, Any]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"exp": expire, "sub": str(subject), "type": "refresh", "jti": str(uuid.uuid4())}, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def get_current_user(db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") == "refresh":
            raise HTTPException(status_code=401, detail="Cannot use refresh token as access token")
        token_data = TokenPayload(**payload)
        if not token_data.sub:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    result = await db.execute(select(User).where(User.id == int(token_data.sub)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

async def verify_elder_access(elder_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role == UserRole.ADMIN or (current_user.role == UserRole.ELDER and current_user.id == elder_id):
        return True
    result = await db.execute(select(UserRelationship).where(UserRelationship.elder_id == elder_id, UserRelationship.caregiver_id == current_user.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Elder not found or not authorized")
    return True


async def has_consent(db: AsyncSession, elder_id: int, kind: str) -> bool:
    from app.models import ElderConsent
    result = await db.execute(select(ElderConsent).where(ElderConsent.elder_id == elder_id, ElderConsent.kind == kind, ElderConsent.revoked_at == None))
    return result.scalar_one_or_none() is not None


async def has_consent(db: AsyncSession, elder_id: int, kind: str) -> bool:
    from app.models import ElderConsent
    result = await db.execute(select(ElderConsent).where(ElderConsent.elder_id == elder_id, ElderConsent.kind == kind, ElderConsent.revoked_at == None))
    return result.scalar_one_or_none() is not None
