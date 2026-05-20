"""
Day 12 — Protocol addition request endpoint.
Saves to Redis list + notifies admin via Telegram.
"""
from __future__ import annotations
import json
import logging
from datetime import datetime, timezone

import httpx
import redis.asyncio as aioredis
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings

log = logging.getLogger(__name__)
router = APIRouter()


class ProtocolRequestBody(BaseModel):
    name: str
    website: str
    github: str = ""
    address: str
    chain: str
    description: str
    email: str
    x_handle: str = ""


def _esc_md(text: str) -> str:
    """Escape MarkdownV2 special chars."""
    specials = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{c}' if c in specials else c for c in str(text))


@router.post("/protocols/request")
async def submit_protocol_request(body: ProtocolRequestBody):
    """
    Submit a protocol for review. Saves to Redis + notifies admin on Telegram.
    """
    if not body.name.strip() or not body.email.strip():
        raise HTTPException(400, "Name and email are required.")

    now = datetime.now(timezone.utc).isoformat()
    record = {
        "name": body.name, "website": body.website, "github": body.github,
        "address": body.address, "chain": body.chain, "description": body.description,
        "email": body.email, "x_handle": body.x_handle, "submitted_at": now,
    }

    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        # Save to Redis list (persistent queue)
        await redis_client.lpush("privascan:protocol_requests", json.dumps(record))

        # Get admin chat ID
        admin_chat_id = await redis_client.get("privascan:admin_chat_id")
    finally:
        await redis_client.aclose()

    # Send Telegram notification
    if admin_chat_id and settings.telegram_bot_token:
        tg_text = (
            "📋 *New Protocol Request*\n\n"
            f"*Protocol:* {_esc_md(body.name)}\n"
            f"*Website:* {_esc_md(body.website)}\n"
            f"*Chain:* {_esc_md(body.chain)}\n"
            f"*Address:* `{_esc_md(body.address)}`\n"
            f"*Contact:* {_esc_md(body.email)}\n"
            f"*X handle:* {_esc_md(body.x_handle or 'not provided')}\n\n"
            f"*Description:*\n{_esc_md(body.description[:400])}"
        )
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                    json={"chat_id": admin_chat_id, "text": tg_text, "parse_mode": "MarkdownV2"},
                )
            log.info("protocol_request.notified admin name=%s", body.name)
        except Exception as exc:
            log.warning("protocol_request.telegram_notify_failed: %s", exc)

    return {"status": "submitted", "message": "Thank you. We review all submissions within 72 hours."}
