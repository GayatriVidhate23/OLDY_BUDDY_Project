import uuid
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any, Union, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import settings, get_db
from app.models import User, UserRole, UserRelationship
from app.schemas import TokenPayload

ALGORITHM = settings.ALGORITHM
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pwd_bytes = plain_password.encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    secret = getattr(settings, "JWT_SECRET_KEY", None) or settings.SECRET_KEY
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return jwt.encode(to_encode, secret, algorithm=ALGORITHM)

def create_refresh_token(subject: Union[str, Any]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    secret = getattr(settings, "JWT_SECRET_KEY", None) or settings.SECRET_KEY
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh", "jti": str(uuid.uuid4())}
    return jwt.encode(to_encode, secret, algorithm=ALGORITHM)

def decode_token(token: str) -> TokenPayload:
    secret = getattr(settings, "JWT_SECRET_KEY", None) or settings.SECRET_KEY
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        return TokenPayload(**payload)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    secret = getattr(settings, "JWT_SECRET_KEY", None) or settings.SECRET_KEY
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        if payload.get("type") == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cannot use refresh token as access token",
            )
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    result = await db.execute(select(User).where(User.id == int(sub)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

def require_role(roles: List[UserRole]):
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
            )
        return current_user
    return role_checker

async def verify_elder_access(
    elder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    if current_user.role == UserRole.ADMIN:
        return True
    if current_user.role == UserRole.ELDER and current_user.id == elder_id:
        return True

    result = await db.execute(
        select(UserRelationship).where(
            UserRelationship.elder_id == elder_id,
            UserRelationship.caregiver_id == current_user.id,
        )
    )
    rel = result.scalar_one_or_none()
    if not rel:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this elder's data",
        )
    return True

