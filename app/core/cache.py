"""
Redis cache wrapper.
Creates a fresh client per call — safe across thread-local event loops
(used by both FastAPI main loop and Slither thread pool loops).
"""

import json
import logging
import redis.asyncio as aioredis
from app.config import settings

log = logging.getLogger(__name__)


def _client() -> aioredis.Redis:
    """Fresh client each call — avoids cross-loop singleton issues."""
    return aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )


def _score_key(chain_slug: str, address: str) -> str:
    return f"score:{chain_slug}:{address.lower()}"


async def get_cached_score(chain_slug: str, address: str) -> dict | None:
    try:
        async with _client() as r:
            raw = await r.get(_score_key(chain_slug, address))
            if raw:
                log.info("cache.hit chain=%s address=%s", chain_slug, address)
                return json.loads(raw)
    except Exception as exc:
        log.warning("cache.get_failed: %s", exc)
    return None


async def set_cached_score(
    chain_slug: str,
    address: str,
    data: dict,
    tvl_source: str = "none",
    scan_type: str = "community",
) -> None:
    try:
        async with _client() as r:
            if scan_type == "curated":
                ttl = settings.score_cache_ttl_curated
            elif tvl_source == "dune_sim":
                ttl = settings.score_cache_ttl_dune
            else:
                ttl = settings.score_cache_ttl_community
            await r.setex(_score_key(chain_slug, address), ttl, json.dumps(data))
            log.info("cache.set chain=%s address=%s ttl=%ds", chain_slug, address, ttl)
    except Exception as exc:
        log.warning("cache.set_failed: %s", exc)


async def invalidate_score(chain_slug: str, address: str) -> None:
    try:
        async with _client() as r:
            await r.delete(_score_key(chain_slug, address))
    except Exception as exc:
        log.warning("cache.invalidate_failed: %s", exc)
