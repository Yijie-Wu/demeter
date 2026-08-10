from fastapi import APIRouter

from app.apis.health import router as health_router


router = APIRouter()
router.include_router(health_router, prefix="/health", tags=["health"])
