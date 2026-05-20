from fastapi import APIRouter
from app.api.v1 import health, score, protocols, keys
from app.api.v1.verify import router as verify_router
from app.api.v1.protocol_requests import router as requests_router

api_router = APIRouter()
api_router.include_router(health.router,    tags=["health"])
api_router.include_router(score.router,     prefix="/score",     tags=["score"])
api_router.include_router(protocols.router, prefix="/protocols", tags=["protocols"])
api_router.include_router(keys.router,      prefix="/keys",      tags=["keys"])
api_router.include_router(verify_router,    tags=["verify"])
api_router.include_router(requests_router,  tags=["protocol-requests"])
