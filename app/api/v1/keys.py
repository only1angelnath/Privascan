"""
Day 11 — API key generation endpoint.

POST /api/v1/keys/generate
Body:    { "email": "user@example.com", "tier": "free" | "pro" }
Returns: { "api_key": "ps_...", "tier": "free", "email": "...", "message": "..." }

Security model:
  - Raw key is returned ONCE — we never store or log it.
  - Only SHA-256(raw_key) is persisted in api_keys.key_hash.
  - Key format: ps_ + 32-byte url-safe random = 46 chars total.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import ApiKey

log = logging.getLogger(__name__)
router = APIRouter()

VALID_TIERS = {"free", "pro"}
RATE_LIMIT_DISPLAY = {"free": 100, "pro": 1000}


class GenerateKeyRequest(BaseModel):
    email: str
    tier: str = "free"


class GenerateKeyResponse(BaseModel):
    api_key: str
    tier: str
    email: str
    message: str


@router.post("/generate", response_model=GenerateKeyResponse)
async def generate_api_key(
    body: GenerateKeyRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a new PrivaScan API key.

    The raw key is returned exactly once and is never stored.
    Subsequent requests with this key must send it as the X-API-Key header.
    """
    # Validate tier
    if body.tier not in VALID_TIERS:
        raise HTTPException(
            status_code=400,
            detail=f"tier must be one of: {sorted(VALID_TIERS)}",
        )

    # Validate email (basic check — no external dependency)
    email = (body.email or "").strip().lower()
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Valid email address required.")

    # Generate cryptographically secure key
    raw_key = f"ps_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    # Collision guard (astronomically unlikely, but correct)
    existing = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=500,
            detail="Key collision detected — please retry.",
        )

    # Persist (hash only — never the raw key)
    db.add(ApiKey(
        id=str(uuid.uuid4()),
        key_hash=key_hash,
        tier=body.tier,
        owner_email=email,
        is_active=True,
    ))

    rate_limit = RATE_LIMIT_DISPLAY.get(body.tier, 100)
    log.info("keys.generated tier=%s email=%s", body.tier, email)

    return GenerateKeyResponse(
        api_key=raw_key,
        tier=body.tier,
        email=email,
        message=(
            f"Store this key safely — it will NOT be shown again. "
            f"Rate limit: {rate_limit} requests/hour. "
            f"Usage: set header  X-API-Key: {raw_key[:8]}..."
        ),
    )
