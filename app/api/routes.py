from fastapi import APIRouter

from app.api.admin import router as admin_router
from app.api.health import router as health_router
from app.api.push import router as push_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(push_router, prefix="/v1", tags=["push"])
router.include_router(admin_router, prefix="/admin", tags=["admin"])
