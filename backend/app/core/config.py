from pydantic_settings import BaseSettings

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
