"""
Day 5 smoke test — Liquidity/TVL Analyser
Uses real TVL data already fetched by the Day 2 collector.
No Slither, no RPC — just math on top of what collector returns.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.core.clients.collector import collect_contract_data
from app.core.scoring.liquidity_analyser import analyse_liquidity


async def test_contract(label: str, address: str, chain_slug: str):
    print(f"\n{'='*60}")
    print(f"Testing : {label}")
    print(f"Address : {address}")
    print("="*60)

    raw = await collect_contract_data(address=address, chain_slug=chain_slug)

    result = analyse_liquidity(
        tvl=raw.tvl,
        address=address,
        chain_id=raw.chain_id,
    )

    print(f"TVL USD       : ${result.tvl_usd:,.2f}" if result.tvl_usd else "TVL USD       : None")
    print(f"TVL source    : {result.tvl_source}")
    print(f"TVL confidence: {result.tvl_confidence}")
    print(f"TVL tier      : {result.tvl_tier}")
    print(f"Risk score    : {result.score}/100")


async def main():
    # Whale — Railgun has ~$86M TVL → expect tier=whale, score~5
    await test_contract(
        label="Railgun Smart Wallet (whale TVL)",
        address="0xfa7093cdd9ee6932b4eb2c9e1cde7ce00b1fa4b9",
        chain_slug="ethereum",
    )

    # Small — Tornado Cash 0.1 ETH pool ~$581 → expect tier=minimal, score~70
    await test_contract(
        label="Tornado Cash 0.1 ETH Pool (minimal TVL)",
        address="0xCC9a0B7c43DC2a5F023Bb9b738E45B0Ef6B06E04",
        chain_slug="ethereum",
    )

    # Curated — Panther Protocol via DefiLlama (high confidence)
    await test_contract(
        label="Panther Protocol ZKP Token (low TVL, high confidence)",
        address="0x909e34d3f6124c324ac83dcca84b74b7029b8ae3",
        chain_slug="polygon",
    )


if __name__ == "__main__":
    asyncio.run(main())
