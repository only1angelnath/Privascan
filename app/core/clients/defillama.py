"""
DefiLlama REST API client — no API key required.
Used for TVL data on curated protocols (Track A).
Docs: https://defillama.com/docs/api
"""

import structlog
from app.core.clients.base import BaseClient
from app.core.models.contract import TvlResult

log = structlog.get_logger()


class DefiLlamaClient(BaseClient):
    base_url = "https://api.llama.fi"

    async def get_protocol_tvl(self, slug: str) -> TvlResult:
        """
        Fetch total TVL for a protocol by its DefiLlama slug.
        e.g. slug = "tornado-cash", "railgun", "aztec"
        """
        log.info("defillama.get_protocol_tvl", slug=slug)
        try:
            data = await self.get(f"/protocol/{slug}")
            tvl = data.get("tvl")

            # tvl can be a list of {date, totalLiquidityUSD} or a flat number
            if isinstance(tvl, list) and tvl:
                current_tvl = tvl[-1].get("totalLiquidityUSD")
            elif isinstance(tvl, (int, float)):
                current_tvl = float(tvl)
            else:
                current_tvl = None

            if current_tvl is not None:
                return TvlResult(
                    protocol_slug=slug,
                    tvl_usd=float(current_tvl),
                    source="defillama",
                    confidence="high",
                )

        except Exception as e:
            log.warning("defillama.fetch_failed", slug=slug, error=str(e))

        return TvlResult(
            protocol_slug=slug,
            tvl_usd=None,
            source="none",
            confidence="none",
        )

    async def get_protocol_chain_tvl(self, slug: str, chain: str) -> TvlResult:
        """
        Fetch TVL for a protocol on a specific chain.
        e.g. slug="railgun", chain="ethereum"
        """
        log.info("defillama.get_chain_tvl", slug=slug, chain=chain)
        try:
            data = await self.get(f"/protocol/{slug}")
            chain_tvls = data.get("chainTvls", {})

            # DefiLlama capitalises chain names e.g. "Ethereum"
            chain_key = chain.capitalize()
            chain_data = chain_tvls.get(chain_key, {})
            tvl_series = chain_data.get("tvl", [])

            if tvl_series:
                current_tvl = tvl_series[-1].get("totalLiquidityUSD")
                if current_tvl is not None:
                    return TvlResult(
                        protocol_slug=slug,
                        chain=chain,
                        tvl_usd=float(current_tvl),
                        source="defillama",
                        confidence="high",
                    )

        except Exception as e:
            log.warning("defillama.chain_fetch_failed", slug=slug, chain=chain, error=str(e))

        return TvlResult(
            protocol_slug=slug,
            chain=chain,
            tvl_usd=None,
            source="none",
            confidence="none",
        )

    async def list_protocols(self) -> list[dict]:
        """Fetch all protocols — used for slug discovery."""
        try:
            return await self.get("/protocols")
        except Exception as e:
            log.error("defillama.list_protocols_failed", error=str(e))
            return []


# Module-level singleton
defillama_client = DefiLlamaClient()
