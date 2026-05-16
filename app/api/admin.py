"""
Day 11 — Admin override resolution endpoint.

POST /admin/override/resolve
Header: X-Admin-Key: <ADMIN_API_KEY from .env>

What this does:
  1. Validates admin key against settings.admin_api_key
  2. Looks up the exploit_record — must exist and be unresolved
  3. Sets exploit_records.is_resolved=True, resolved_at=now
  4. Inserts a row into override_history (audit trail)
  5. Invalidates Redis score cache for the affected address (all chains)
  6. Returns updated status

After this call, the exploit_active override is removed.
The next GET /score/{chain}/{address} will compute a fresh composite score
without the exploit cap (score capped at 30, grade F).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.db.models import Contract, ExploitRecord, OverrideHistory

log = logging.getLogger(__name__)
router = APIRouter()

VALID_RESOLUTION_TYPES = {"remediated", "compensated", "redeployed"}


# ── Admin key guard ───────────────────────────────────────────────────────────

def verify_admin_key(x_admin_key: str | None = Header(default=None)) -> None:
    """FastAPI dependency — validates X-Admin-Key header."""
    if not x_admin_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing admin key.")


# ── Schemas ───────────────────────────────────────────────────────────────────

class ResolveOverrideRequest(BaseModel):
    protocol_id: str            # UUID of the protocol
    exploit_record_id: str      # UUID of the exploit_record to resolve
    resolution_type: str        # remediated | compensated | redeployed
    resolution_evidence: str    # URL to post-mortem / disclosure link
    resolution_note: str = ""   # optional free-text note


class ResolveOverrideResponse(BaseModel):
    status: str
    exploit_record_id: str
    protocol_id: str
    resolution_type: str
    resolved_at: str
    cache_invalidated: bool
    note: str


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/override/resolve", response_model=ResolveOverrideResponse)
async def resolve_override(
    body: ResolveOverrideRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin_key),
):
    """
    Resolve an active exploit override.

    After a successful call:
    - exploit_records row: is_resolved=True, resolved_at=<now>
    - override_history row: inserted with resolution details
    - Redis cache: invalidated for the affected address
    - Next score request: computes fresh composite (no exploit cap)
    """

    # Validate resolution_type
    if body.resolution_type not in VALID_RESOLUTION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"resolution_type must be one of: {sorted(VALID_RESOLUTION_TYPES)}",
        )

    # Validate evidence URL
    if not body.resolution_evidence.strip():
        raise HTTPException(
            status_code=400,
            detail="resolution_evidence (post-mortem URL) is required.",
        )

    # ── 1. Fetch exploit record ───────────────────────────────────────────────
    exploit_result = await db.execute(
        select(ExploitRecord).where(ExploitRecord.id == body.exploit_record_id)
    )
    exploit = exploit_result.scalar_one_or_none()

    if not exploit:
        raise HTTPException(
            status_code=404,
            detail=f"Exploit record '{body.exploit_record_id}' not found.",
        )

    if exploit.is_resolved:
        raise HTTPException(
            status_code=409,
            detail="This exploit record is already marked as resolved.",
        )

    now = datetime.now(timezone.utc)

    # ── 2. Mark exploit as resolved ───────────────────────────────────────────
    await db.execute(
        update(ExploitRecord)
        .where(ExploitRecord.id == body.exploit_record_id)
        .values(is_resolved=True, resolved_at=now)
    )

    # ── 3. Find contract row for this address (to link override_history) ──────
    contract_id = None
    if exploit.contract_address:
        contract_result = await db.execute(
            select(Contract).where(
                Contract.address == exploit.contract_address.lower()
            )
        )
        contract = contract_result.scalar_one_or_none()
        if contract:
            contract_id = contract.id

    # ── 4. Insert override_history audit trail row ────────────────────────────
    db.add(OverrideHistory(
        id=str(uuid.uuid4()),
        contract_id=contract_id,
        protocol_id=body.protocol_id or None,
        override_type="exploit",
        override_status="resolved",
        applied_at=now,
        resolved_at=now,
        resolution_type=body.resolution_type,
        resolution_evidence=body.resolution_evidence.strip(),
        resolution_note=body.resolution_note.strip() or None,
        resolved_by="admin",
    ))

    # ── 5. Invalidate Redis cache for affected address ────────────────────────
    cache_invalidated = False
    if exploit.contract_address:
        try:
            redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
            try:
                # Score cache keys: privascan:score:{chain}:{address}
                # Scan all chains for this address
                pattern = f"privascan:score:*:{exploit.contract_address.lower()}"
                deleted = 0
                async for key in redis_client.scan_iter(match=pattern):
                    await redis_client.delete(key)
                    deleted += 1
                if deleted > 0:
                    log.info(
                        "admin.cache_invalidated address=%s keys_deleted=%d",
                        exploit.contract_address, deleted,
                    )
                    cache_invalidated = True
            finally:
                await redis_client.aclose()
        except Exception as exc:
            # Cache invalidation failure is non-fatal — log and continue
            log.warning("admin.cache_invalidation_failed: %s", exc)

    log.info(
        "admin.override_resolved exploit_id=%s protocol_id=%s type=%s by=admin",
        body.exploit_record_id, body.protocol_id, body.resolution_type,
    )

    return ResolveOverrideResponse(
        status="resolved",
        exploit_record_id=body.exploit_record_id,
        protocol_id=body.protocol_id,
        resolution_type=body.resolution_type,
        resolved_at=now.isoformat(),
        cache_invalidated=cache_invalidated,
        note=(
            "Exploit override removed. The next score request for this address "
            "will compute a fresh composite without the exploit cap."
        ),
    )
