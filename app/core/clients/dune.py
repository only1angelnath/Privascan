"""
Dune SIM API client — real-time on-chain balance reads.
Used as TVL fallback for community scans (Track B).
SIM API docs: https://docs.sim.dune.com
"""

import structlog
from app.core.clients.base import BaseClient
from app.core.models.contract import TvlResult
from app.config import settings

log = structlog.get_logger()


class DuneSimClient(BaseClient):
    base_url = "https://api.sim.dune.com"

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "X-Sim-Api-Key": settings.dune_api_key,   # correct header name
        }

    async def _get_client(self):
        # Always create a fresh client per call.
        # Celery workers call asyncio.run() repeatedly, which destroys the
        # event loop each time. A cached httpx.AsyncClient becomes stale
        # after the first loop closes, causing 'Event loop is closed'.
        import httpx
        from app.core.clients.base import DEFAULT_TIMEOUT
        return httpx.AsyncClient(
            base_url=self.base_url,
            timeout=DEFAULT_TIMEOUT,
            headers=self._headers(),
            follow_redirects=True,
        )

    async def get_contract_balance_usd(
        self, address: str, chain_slug: str
    ) -> TvlResult:
        """
        Get total USD value of tokens held by a contract address.
        Filters out spam tokens, unpriced tokens, and low-liquidity tokens
        to prevent TVL inflation from fake/scam assets.
        Only reads first page — sufficient for contract TVL (not whale wallets).
        """
        log.info("dune_sim.get_balance", address=address, chain=chain_slug)

        chain_id = _to_chain_id(chain_slug)

        try:
            params = {
                "chain_ids": chain_id,
                "exclude_spam_tokens": "true",
                "exclude_unpriced": "true",
            }

            data = await self.get(
                f"/v1/evm/balances/{address}",
                params=params,
            )

            balances = data.get("balances", [])

            # Also exclude low-liquidity tokens — prevents fake TVL from
            # scam contracts holding illiquid tokens with absurd prices
            total_usd = sum(
                float(b.get("value_usd", 0) or 0)
                for b in balances
                if not b.get("low_liquidity", False)
            )

            if total_usd > 0:
                return TvlResult(
                    contract_address=address,
                    chain=chain_slug,
                    tvl_usd=total_usd,
                    source="dune_sim",
                    confidence="medium",
                )
            else:
                return TvlResult(
                    contract_address=address,
                    chain=chain_slug,
                    tvl_usd=None,
                    source="dune_sim",
                    confidence="low",
                )

        except Exception as e:
            log.warning("dune_sim.fetch_failed", address=address, error=str(e))
            return TvlResult(
                contract_address=address,
                chain=chain_slug,
                tvl_usd=None,
                source="none",
                confidence="none",
            )


def _to_chain_id(slug: str) -> int:
    """Map chain slug to numeric chain ID for SIM API filter."""
    mapping = {
        "ethereum": 1,
        "polygon": 137,
        "arbitrum": 42161,
        "optimism": 10,
        "base": 8453,
        "bnb": 56,
        "avalanche": 43114,
    }
    return mapping.get(slug, 1)


# Module-level singleton
dune_sim_client = DuneSimClient()
