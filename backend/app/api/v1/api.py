from fastapi import APIRouter
from app.api.v1.endpoints import auth, elders, activities

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(elders.router, prefix="/elders", tags=["elders"])
api_router.include_router(activities.router, prefix="/elders", tags=["activities"])
