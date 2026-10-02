import os

base = r"c:\Users\gayat\Documents\OLDY_BUDDY_Project\backend"

files = {}

files["requirements.txt"] = """fastapi>=0.100.0
uvicorn[standard]>=0.22.0
sqlalchemy>=2.0.0
alembic>=1.11.0
psycopg2-binary>=2.9.6
asyncpg>=0.28.0
redis>=4.6.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
passlib[bcrypt]
argon2-cffi
python-jose[cryptography]
pytest
pytest-asyncio
httpx
"""

files[".env.example"] = """PROJECT_NAME="Oldy Buddy API"
API_V1_STR="/api/v1"
SECRET_KEY="supersecretkey"
ACCESS_TOKEN_EXPIRE_MINUTES=11520
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/oldybuddy"
REDIS_URL="redis://localhost:6379/0"
"""

files["Dockerfile"] = """FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

files["docker-compose.yml"] = """version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/oldybuddy
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=oldybuddy
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
  redis:
    image: redis:7
    ports:
      - "6379:6379"
volumes:
  pgdata:
"""

files["app/core/config.py"] = """from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Oldy Buddy API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520 # 8 days
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"  # fallback
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"

settings = Settings()
"""

files["app/core/security.py"] = """from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
ALGORITHM = "HS256"

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
"""

files["app/db/database.py"] = """from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
"""

files["app/models/user.py"] = """from sqlalchemy import Column, Integer, String, Boolean, Enum
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
"""

files["app/models/elder_profile.py"] = """from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from app.db.database import Base

class ElderProfile(Base):
    __tablename__ = "elder_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    preferences = Column(JSON, default={})
    medical_info = Column(JSON, default={})
    emergency_contact = Column(String)
"""

files["app/models/relationship.py"] = """from sqlalchemy import Column, Integer, ForeignKey, Enum
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
"""

files["app/models/activity.py"] = """from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from app.db.database import Base
from datetime import datetime, timezone

class ActivityType(str, enum=True):
    REMINDER = "REMINDER"
    CHECK_IN = "CHECK_IN"
    SOS = "SOS"

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    elder_id = Column(Integer, ForeignKey("users.id"))
    activity_type = Column(String, nullable=False)
    description = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String, default="PENDING")
"""

files["app/schemas/user.py"] = """from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.ELDER

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
"""

files["app/schemas/elder.py"] = """from pydantic import BaseModel
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
"""

files["app/schemas/activity.py"] = """from pydantic import BaseModel
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
"""

files["app/api/deps.py"] = """from typing import Generator, Optional
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
"""

files["app/api/v1/endpoints/auth.py"] = """from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api import deps
from app.core import security
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserResponse

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="The user with this username already exists in the system.")
    db_user = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token = security.create_access_token(user.id)
    return {"access_token": access_token, "token_type": "bearer"}
"""

files["app/api/v1/endpoints/elders.py"] = """from fastapi import APIRouter, Depends, HTTPException
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
    profile = ElderProfile(**profile_in.model_dump(), user_id=elder_id)
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile
"""

files["app/api/v1/endpoints/activities.py"] = """from fastapi import APIRouter, Depends, HTTPException
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
"""

files["app/api/v1/api.py"] = """from fastapi import APIRouter
from app.api.v1.endpoints import auth, elders, activities

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(elders.router, prefix="/elders", tags=["elders"])
api_router.include_router(activities.router, prefix="/elders", tags=["activities"])
"""

files["app/main.py"] = """from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.api import api_router

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health():
    return {"status": "ok"}
"""

files["app/intelligence/context_engine.py"] = """class ContextEngine:
    async def get_context(self, elder_id: int, db) -> dict:
        # Mock fetch from DB/Redis
        return {"current_mood": "calm", "last_activity": "medicine"}
"""

files["app/intelligence/intent_engine.py"] = """class IntentEngine:
    async def infer_intent(self, user_input: str) -> str:
        # Mock LLM interaction
        if "help" in user_input.lower() or "sos" in user_input.lower():
            return "SOS"
        return "GENERAL"
"""

files["app/intelligence/policy_engine.py"] = """class PolicyEngine:
    async def validate_action(self, intent: str, context: dict) -> bool:
        # Deterministic logic overriding LLM
        if intent == "SOS":
            return True # Always allow SOS
        return True
"""

files["app/intelligence/workflow_engine.py"] = """from app.models.activity import Activity
from app.intelligence.context_engine import ContextEngine
from app.intelligence.policy_engine import PolicyEngine

context_engine = ContextEngine()
policy_engine = PolicyEngine()

async def process_activity(activity: Activity, db):
    context = await context_engine.get_context(activity.elder_id, db)
    # Perform deterministic checks and side effects (like sending notifications)
    is_valid = await policy_engine.validate_action(activity.activity_type, context)
    if is_valid and activity.activity_type == "SOS":
        # e.g., create alert, send notification
        pass
"""

files["alembic.ini"] = """[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql+asyncpg://postgres:postgres@localhost:5432/oldybuddy

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""

files["alembic/env.py"] = """import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.db.database import Base
from app.models.user import User
from app.models.elder_profile import ElderProfile
from app.models.relationship import UserRelationship
from app.models.activity import Activity
from app.core.config import settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite+pysqlite") if "sqlite" in settings.DATABASE_URL else settings.DATABASE_URL)

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    # Handle asyncio loop for async sqlalchemy
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(run_async_migrations())
    else:
        # If there's an event loop running, we create a task
        # This is unlikely in standard alembic execution
        pass

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""

files["pytest.ini"] = """[pytest]
asyncio_mode = auto
"""

files["tests/conftest.py"] = """import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.database import Base, get_db
from app.main import app
from app.core.config import settings
import asyncio

# Setup test db
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module", autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db():
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture
async def client(db: AsyncSession):
    async def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
"""

files["tests/test_auth.py"] = """import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password", "role": "ELDER", "full_name": "Test User"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    # Registration should already be done if run in order, but let's re-register or ignore 400
    await client.post(
        "/api/v1/auth/register",
        json={"email": "test2@example.com", "password": "password", "role": "ELDER", "full_name": "Test User"}
    )
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test2@example.com", "password": "password"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
"""

files["tests/test_elders.py"] = """import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_elder_profile(client: AsyncClient):
    # Register an elder
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "elder1@example.com", "password": "pass", "role": "ELDER"}
    )
    assert reg.status_code == 200
    elder_id = reg.json()["id"]

    # Login
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": "elder1@example.com", "password": "pass"}
    )
    token = login.json()["access_token"]
    
    # Create profile
    headers = {"Authorization": f"Bearer {token}"}
    prof_create = await client.post(
        f"/api/v1/elders/{elder_id}/profile",
        headers=headers,
        json={"user_id": elder_id, "emergency_contact": "911"}
    )
    assert prof_create.status_code == 200
    assert prof_create.json()["emergency_contact"] == "911"
    
    # Get profile
    prof_get = await client.get(
        f"/api/v1/elders/{elder_id}/profile",
        headers=headers
    )
    assert prof_get.status_code == 200
"""

files["tests/test_activities.py"] = """import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_sos_activity(client: AsyncClient):
    reg = await client.post("/api/v1/auth/register", json={"email": "elder_act@example.com", "password": "pass", "role": "ELDER"})
    elder_id = reg.json()["id"]
    login = await client.post("/api/v1/auth/login", data={"username": "elder_act@example.com", "password": "pass"})
    token = login.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    act = await client.post(
        f"/api/v1/elders/{elder_id}/activities",
        headers=headers,
        json={"activity_type": "SOS", "description": "Fallen down"}
    )
    assert act.status_code == 200
    assert act.json()["activity_type"] == "SOS"
"""

files["README.md"] = """# Oldy Buddy Backend

Clean modular monolith backend for Oldy Buddy.

## Features
- Authentication & RBAC (Elder, Caregiver, Family, Admin)
- Elder Profiles & Activities
- Intelligence Architecture (Context, Intent, Policy, Workflow Engines)

## Setup
```bash
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
docker-compose up -d db redis
alembic upgrade head
uvicorn app.main:app --reload
```

## Testing
```bash
pytest
```
"""

import os
for path, content in files.items():
    full_path = os.path.join(base, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Advanced files created.")
