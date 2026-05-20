"""
GET /api/v1/keys/usage
Returns usage stats for an API key from Redis counters.
"""

from fastapi import APIRouter, Header
from datetime import datetime, timezone
import hashlib

import redis.asyncio as aioredis
from app.config import settings

router = APIRouter()


def _redis():
    return aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )


@router.get("/usage")
async def get_usage(x_api_key: str = Header(..., alias="X-API-Key")):
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    prefix = key_hash[:16]

    async with _redis() as r:
        total_raw     = await r.get(f"usage:{prefix}:total")
        today         = datetime.now(timezone.utc).strftime("%Y%m%d")
        today_raw     = await r.get(f"usage:{prefix}:d:{today}")
        min_used_raw  = await r.get(f"ratemin:free:{prefix}")
        hour_used_raw = await r.get(f"rate:free:{prefix}")

    return {
        "key_prefix":      prefix,
        "total_requests":  int(total_raw)     if total_raw     else 0,
        "today_requests":  int(today_raw)     if today_raw     else 0,
        "rate_limit": {
            "per_minute": {
                "limit": settings.rate_limit_free,
                "used":  int(min_used_raw)  if min_used_raw  else 0,
            },
            "per_hour": {
                "limit": settings.rate_limit_free * 10,
                "used":  int(hour_used_raw) if hour_used_raw else 0,
            },
        },
    }
