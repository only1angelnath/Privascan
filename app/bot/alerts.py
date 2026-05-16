"""
Day 10 — Redis pub/sub alert system.
Tasks publish to 'privascan:alerts' channel.
Bot subscribes and dispatches Telegram messages.
"""

from __future__ import annotations
import asyncio
import json
import logging

import redis.asyncio as aioredis

from app.config import settings

log = logging.getLogger(__name__)

ALERT_CHANNEL = "privascan:alerts"


async def publish_alert(payload: dict) -> None:
    """
    Publish a score change alert to Redis.
    Called from Celery tasks (via asyncio.run).
    """
    try:
        r = aioredis.from_url(settings.redis_url, decode_responses=True)
        await r.publish(ALERT_CHANNEL, json.dumps(payload))
        await r.aclose()
        log.info("alert.published address=%s chat_id=%s",
                 payload.get("address"), payload.get("chat_id"))
    except Exception as exc:
        log.error("alert.publish_failed: %s", exc)


class AlertSubscriber:
    """
    Async Redis subscriber. Runs as a background task inside the bot.
    On each message, calls the provided dispatch callback.
    """

    def __init__(self, dispatch_fn):
        self._dispatch = dispatch_fn
        self._running = False

    async def run(self) -> None:
        self._running = True
        log.info("alert_subscriber.start channel=%s", ALERT_CHANNEL)

        while self._running:
            try:
                r = aioredis.from_url(settings.redis_url, decode_responses=True)
                pubsub = r.pubsub()
                await pubsub.subscribe(ALERT_CHANNEL)
                log.info("alert_subscriber.subscribed")

                async for message in pubsub.listen():
                    if not self._running:
                        break
                    if message["type"] != "message":
                        continue
                    try:
                        payload = json.loads(message["data"])
                        await self._dispatch(payload)
                    except Exception as exc:
                        log.error("alert_subscriber.dispatch_error: %s", exc)

                await pubsub.unsubscribe(ALERT_CHANNEL)
                await r.aclose()

            except Exception as exc:
                log.error("alert_subscriber.connection_error: %s", exc)
                if self._running:
                    await asyncio.sleep(5)  # reconnect after 5s

    def stop(self) -> None:
        self._running = False
