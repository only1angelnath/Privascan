"""
Day 12 — Telegram verification + Usage tracking endpoints.
"""
from __future__ import annotations
import hashlib
import logging
from datetime import datetime, timezone, timedelta

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.db.models import ApiKey

log = logging.getLogger(__name__)
router = APIRouter()


class VerifyRequest(BaseModel):
    code: str


@router.post("/keys/verify-telegram")
async def verify_telegram_code(body: VerifyRequest):
    """
    Validate a 6-digit code sent by @PrivaScanBot.
    Returns telegram_user_id on success. Code is consumed (one-time use).
    """
    code = body.code.strip()
    if not code.isdigit() or len(code) != 6:
        raise HTTPException(400, "Code must be exactly 6 digits. Send /verify to @PrivaScanBot for a new one.")

    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        telegram_id = await redis_client.get(f"verify:{code}")
        if not telegram_id:
            raise HTTPException(400, "Invalid or expired code. Send /verify to @PrivaScanBot to get a fresh one.")
        await redis_client.delete(f"verify:{code}")
        log.info("verify.success telegram_id=%s", telegram_id)
        return {"valid": True, "telegram_user_id": telegram_id}
    finally:
        await redis_client.aclose()


@router.get("/keys/usage")
async def get_key_usage(key: str, db: AsyncSession = Depends(get_db)):
    """
    Return detailed usage stats for an API key.
    """
    if not key.startswith("ps_"):
        raise HTTPException(400, "Invalid API key format.")

    key_hash = hashlib.sha256(key.encode()).hexdigest()
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
    )
    api_key_row = result.scalar_one_or_none()
    if not api_key_row:
        raise HTTPException(404, "API key not found or inactive.")

    prefix = key_hash[:16]
    LIMITS = {"anonymous": 10, "free": 500, "pro": 2000}
    tier_limit = LIMITS.get(api_key_row.tier, 500)

    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        now = datetime.now(timezone.utc)

        # All-time total
        total = int(await redis_client.get(f"usage:{prefix}:total") or 0)

        # Current hour
        hour_key = f"rate:{api_key_row.tier}:{prefix}"
        hour_used = int(await redis_client.get(hour_key) or 0)
        hour_ttl  = await redis_client.ttl(hour_key)

        # Last 7 days
        last_7 = []
        for i in range(7):
            d = (now - timedelta(days=i)).strftime('%Y%m%d')
            count = int(await redis_client.get(f"usage:{prefix}:d:{d}") or 0)
            label = (now - timedelta(days=i)).strftime('%b %d')
            last_7.append({"date": d, "label": label, "requests": count})

        return {
            "key_prefix": key[:10] + "...",
            "tier": api_key_row.tier,
            "email": api_key_row.owner_email,
            "created_at": api_key_row.created_at.isoformat() if api_key_row.created_at else None,
            "rate_limits": {
                "per_minute": {"anonymous": 2, "free": 15, "pro": 60}.get(api_key_row.tier, 15),
                "per_hour": tier_limit,
            },
            "current_hour": {
                "used": hour_used,
                "remaining": max(0, tier_limit - hour_used),
                "resets_in_seconds": max(0, int(hour_ttl)) if hour_ttl and hour_ttl > 0 else 3600,
            },
            "all_time": {"total_requests": total},
            "last_7_days": list(reversed(last_7)),
        }
    finally:
        await redis_client.aclose()
