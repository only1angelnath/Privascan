"""
Data collector — orchestrates all API clients to assemble
a complete RawContractData object for the scoring engine.
Called by Celery tasks, not directly by FastAPI endpoints.
"""

import asyncio
import structlog
from app.core.clients.etherscan import etherscan_client
from app.core.clients.alchemy import alchemy_client
from app.core.clients.defillama import defillama_client
from app.core.clients.dune import dune_sim_client
from app.core.models.contract import RawContractData, TvlResult

log = structlog.get_logger()


async def collect_contract_data(
    address: str,
    chain_slug: str,
    protocol_defillama_slug: str | None = None,
    scan_type: str = "community",
) -> RawContractData:
    """
    Fetch all raw data for a contract in parallel where possible.

    For curated protocols (scan_type="curated"):
      - TVL comes from DefiLlama (high confidence)

    For community scans (scan_type="community"):
      - TVL comes from Dune SIM balance read (medium confidence)

    Args:
        address: EVM contract address (0x...)
        chain_slug: e.g. "ethereum", "polygon"
        protocol_defillama_slug: e.g. "tornado-cash" — only for curated
        scan_type: "curated" | "community"

    Returns:
        RawContractData with all available fields populated
    """
    from app.core.clients.chains import get_chain
    chain = get_chain(chain_slug)

    log.info(
        "collector.start",
        address=address,
        chain=chain_slug,
        scan_type=scan_type,
    )

    # ── Fetch source, creation, bytecode, on-chain state in parallel ──
    source_task    = etherscan_client.get_source_code(address, chain_slug)
    creation_task  = etherscan_client.get_contract_creation(address, chain_slug)
    bytecode_task  = alchemy_client.get_bytecode(address, chain_slug)
    on_chain_task  = alchemy_client.get_on_chain_state(address, chain_slug)

    source, creation, bytecode, on_chain = await asyncio.gather(
        source_task,
        creation_task,
        bytecode_task,
        on_chain_task,
        return_exceptions=True,
    )

    # Gracefully handle any individual fetch failures
    source    = source    if not isinstance(source, Exception)    else None
    creation  = creation  if not isinstance(creation, Exception)  else None
    bytecode  = bytecode  if not isinstance(bytecode, Exception)  else None
    on_chain  = on_chain  if not isinstance(on_chain, Exception)  else None

    # ── TVL fetch ──────────────────────────────────────────────────────
    tvl: TvlResult | None = None

    if scan_type == "curated" and protocol_defillama_slug:
        tvl = await defillama_client.get_protocol_chain_tvl(
            protocol_defillama_slug, chain_slug
        )
    else:
        # Community scan — use Dune SIM balance fallback
        tvl = await dune_sim_client.get_contract_balance_usd(address, chain_slug)

    log.info(
        "collector.complete",
        address=address,
        chain=chain_slug,
        verified=getattr(source, "is_verified", False),
        tvl_usd=getattr(tvl, "tvl_usd", None),
        tvl_source=getattr(tvl, "source", "none"),
    )

    return RawContractData(
        address=address,
        chain_id=chain.chain_id,
        chain_slug=chain_slug,
        source=source,
        creation=creation,
        bytecode=bytecode,
        on_chain=on_chain,
        tvl=tvl,
    )
