"""
Base async HTTP client with retry logic, timeouts, and rate-limit handling.
All API clients inherit from this.
"""

import asyncio
import structlog
import httpx
from typing import Any

log = structlog.get_logger()

# Shared timeout for all external calls
DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)


class BaseClient:
    """
    Async HTTP client base class.
    Subclasses set base_url and optionally override _headers().
    """

    base_url: str = ""
    max_retries: int = 3
    retry_backoff: float = 1.5   # seconds — multiplied each retry

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=DEFAULT_TIMEOUT,
                headers=self._headers(),
                follow_redirects=True,
            )
        return self._client

    def _headers(self) -> dict[str, str]:
        return {"Accept": "application/json"}

    async def get(self, url: str, params: dict | None = None) -> Any:
        """GET with automatic retry on 429 and 5xx."""
        client = await self._get_client()
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = await client.get(url, params=params)

                if resp.status_code == 429:
                    wait = self.retry_backoff * attempt
                    log.warning("client.rate_limited", url=url, attempt=attempt, wait=wait)
                    await asyncio.sleep(wait)
                    continue

                if resp.status_code >= 500:
                    wait = self.retry_backoff * attempt
                    log.warning("client.server_error", url=url, status=resp.status_code, attempt=attempt)
                    await asyncio.sleep(wait)
                    continue

                resp.raise_for_status()
                return resp.json()

            except httpx.TimeoutException as e:
                wait = self.retry_backoff * attempt
                log.warning("client.timeout", url=url, attempt=attempt, wait=wait)
                last_error = e
                await asyncio.sleep(wait)

            except httpx.HTTPStatusError as e:
                log.error("client.http_error", url=url, status=e.response.status_code)
                raise

        raise last_error or RuntimeError(f"Failed after {self.max_retries} retries: {url}")

    async def post(self, url: str, json: dict | None = None) -> Any:
        """POST with automatic retry on 429 and 5xx."""
        client = await self._get_client()
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = await client.post(url, json=json)

                if resp.status_code == 429:
                    wait = self.retry_backoff * attempt
                    await asyncio.sleep(wait)
                    continue

                if resp.status_code >= 500:
                    await asyncio.sleep(self.retry_backoff * attempt)
                    continue

                resp.raise_for_status()
                return resp.json()

            except httpx.TimeoutException as e:
                last_error = e
                await asyncio.sleep(self.retry_backoff * attempt)

            except httpx.HTTPStatusError as e:
                log.error("client.http_error", url=url, status=e.response.status_code)
                raise

        raise last_error or RuntimeError(f"POST failed after {self.max_retries} retries: {url}")

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
