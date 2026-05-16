from fastapi import APIRouter
from app.api.v1 import health, score, protocols, keys

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(score.router, prefix="/score", tags=["score"])
api_router.include_router(protocols.router, prefix="/protocols", tags=["protocols"])
api_router.include_router(keys.router, prefix="/keys", tags=["keys"])
