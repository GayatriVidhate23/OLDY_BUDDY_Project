import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

class Settings(BaseSettings):
    PROJECT_NAME: str = "Oldy Buddy API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "oldy-buddy-super-secret-key-change-in-production")
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "oldy-buddy-super-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./oldy_buddy.db")
    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()

if not settings.JWT_SECRET_KEY:
    settings.JWT_SECRET_KEY = settings.SECRET_KEY

# Async SQLAlchemy Engine & Session
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

