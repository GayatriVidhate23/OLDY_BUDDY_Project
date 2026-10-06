from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import time
import os

from app.database import settings, get_db, init_db
# pratham used api_router, main used router. Let's import it as api_router
from app.api import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if hasattr(settings, "API_V1_STR") else "/openapi.json",
    lifespan=lifespan,
)

# Stricter CORS for production
allow_origins = ["*"] if getattr(settings, 'DEBUG', False) else [os.environ.get("FRONTEND_URL", "https://oldybuddy.com")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

if hasattr(settings, "API_V1_STR"):
    app.include_router(api_router, prefix=settings.API_V1_STR)
else:
    app.include_router(api_router, prefix="/api")

@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "Oldy Buddy Backend"}

@app.get("/readyz")
async def readyz(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "db": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service Unavailable")

@app.get("/")
async def root():
    return {"message": "Welcome to Oldy Buddy API", "docs": "/docs"}
