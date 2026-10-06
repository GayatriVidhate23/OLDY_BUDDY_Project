
from fastapi import FastAPI, Depends, HTTPException
from app.api import router
from app.database import settings, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
import time
import os

app = FastAPI(title=settings.PROJECT_NAME, docs_url="/docs" if settings.DEBUG else None, redoc_url=None)

# Stricter CORS for production
allow_origins = ["*"] if settings.DEBUG else [os.environ.get("FRONTEND_URL", "https://oldybuddy.com")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/readyz")
async def readyz(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "db": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service Unavailable")
