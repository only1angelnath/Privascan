from fastapi import APIRouter
from app.config import settings

router = APIRouter()

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "env": settings.app_env,
        "version": "1.0.0",
        "service": "privascan-api",
    }
