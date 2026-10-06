from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Oldy Buddy API"
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    DEBUG: bool = False
    OTP_SECRET: str = os.environ.get("OTP_SECRET", "")

    class Config:
        env_file = ".env"

settings = Settings()

if not settings.JWT_SECRET_KEY or settings.JWT_SECRET_KEY in ["secret", "supersecretkey", "changeme"]:
    if not os.environ.get("PYTEST_CURRENT_TEST"):
        raise RuntimeError("CRITICAL: Insecure or missing JWT_SECRET_KEY in environment!")
    else:
        settings.JWT_SECRET_KEY = "test_safe_secret_key_for_pytest_only"

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
