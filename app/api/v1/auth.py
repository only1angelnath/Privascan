"""
Day 11 — API Key Auth + Rate Limiting dependency.

Usage in any endpoint:
    from app.api.v1.auth import get_api_key

    @router.get("/something")
    async def my_endpoint(
        request: Request,
        api_key_info: dict = Depends(get_api_key),
    ):
        ...

Rate limits (requests/hour):
    Anonymous  — 10   (no X-API-Key header, identified by IP)
    Free       — 100  (valid key, tier=free)
    Pro        — 1000 (valid key, tier=pro)

Redis key format:  rate:{tier}:{identifier}
    - Anonymous:  identifier = client IP
    - Keyed:      identifier = first 16 chars of key_hash
TTL: 3600s (sliding window resets after 1 hour)
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.db.models import ApiKey

log = logging.getLogger(__name__)

RATE_LIMITS: dict[str, int] = {
    "anonymous": settings.rate_limit_anonymous,
    "free":      settings.rate_limit_free,
    "pro":       settings.rate_limit_pro,
}


def _hash_key(raw_key: str) -> str:
    """SHA-256 hash of the raw API key. Only the hash is ever stored or checked."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def get_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    FastAPI dependency — resolves tier and enforces per-hour rate limit.

    Returns:
        {"tier": "anonymous"|"free"|"pro", "key_hash": str|None, "identifier": str}

    Raises:
        401 — key provided but not found or is_active=False
        429 — rate limit exceeded (Retry-After header included)
    """
    tier = "anonymous"
    key_hash = None
    client_ip = (request.client.host if request.client else "unknown") or "unknown"
    identifier = client_ip  # anonymous traffic keyed by IP

    # ── Resolve provided key ──────────────────────────────────────────────────
    if x_api_key:
        key_hash = _hash_key(x_api_key)

        result = await db.execute(
            select(ApiKey).where(
                ApiKey.key_hash == key_hash,
                ApiKey.is_active == True,  # noqa: E712
            )
        )
        api_key_row = result.scalar_one_or_none()

        if api_key_row is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid or inactive API key.",
            )

        tier = api_key_row.tier
        identifier = key_hash[:16]  # short prefix — never log or expose full hash

        # Update last_used_at (best-effort — never fail the request over this)
        try:
            await db.execute(
                update(ApiKey)
                .where(ApiKey.key_hash == key_hash)
                .values(last_used_at=datetime.now(timezone.utc))
            )
        except Exception as exc:
            log.warning("auth.last_used_update_failed: %s", exc)

    # ── Rate limit via Redis ──────────────────────────────────────────────────
    redis_key = f"rate:{tier}:{identifier}"
    limit = RATE_LIMITS.get(tier, RATE_LIMITS["anonymous"])

    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        count = await redis_client.incr(redis_key)
        if count == 1:
            # First hit in this window — arm the 1-hour TTL
            await redis_client.expire(redis_key, 3600)

        if count > limit:
            ttl = await redis_client.ttl(redis_key)
            retry_after = max(int(ttl), 0)
            log.warning(
                "auth.rate_limited tier=%s identifier=%s count=%d limit=%d ttl=%d",
                tier, identifier, count, limit, retry_after,
            )
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Rate limit exceeded: {limit} requests/hour for {tier} tier. "
                    f"Upgrade at privascan.xyz or retry after {retry_after}s."
                ),
                headers={"Retry-After": str(retry_after)},
            )
    finally:
        await redis_client.aclose()

    log.debug(
        "auth.ok tier=%s identifier=%s count=%d/%d",
        tier, identifier, count, limit,
    )
    return {"tier": tier, "key_hash": key_hash, "identifier": identifier}
