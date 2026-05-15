"""
Day 4 smoke test — Ownership Analyser
Tests three contracts with different ownership structures.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.core.clients.collector import collect_contract_data
from app.core.scoring.ownership_analyser import analyse_ownership


async def test_contract(label: str, address: str, chain_slug: str):
    print(f"\n{'='*60}")
    print(f"Testing : {label}")
    print(f"Address : {address}")
    print(f"Chain   : {chain_slug}")
    print("="*60)

    raw = await collect_contract_data(address=address, chain_slug=chain_slug)

    # RawContractData fields are: .source  .on_chain  (not .source_code / .on_chain_state)
    source = ""
    if raw.source and raw.source.source_code:
        source = raw.source.source_code

    on_chain = raw.on_chain
    if on_chain is None:
        print("ERROR: on_chain data not available")
        return

    result = await analyse_ownership(
        on_chain=on_chain,
        source_code=source,
        chain_slug=chain_slug,
        code_flags=[],
    )

    print(f"Owner address : {result.details.get('owner_address', 'n/a')}")
    print(f"Is renounced  : {result.details['is_renounced']}")
    print(f"Is multisig   : {result.details['is_multisig']}")
    print(f"Is EOA        : {result.details['is_eoa']}")
    print(f"Has timelock  : {result.details['has_timelock']}")
    print(f"TL delay (h)  : {result.details.get('timelock_delay_hours')}")
    print(f"Flags         : {result.flags}")
    print(f"Risk score    : {result.score}/100")


async def main():
    # EOA-controlled — expect owner-is-eoa, score ~45
    await test_contract(
        label="Tornado Cash 0.1 ETH Pool",
        address="0xCC9a0B7c43DC2a5F023Bb9b738E45B0Ef6B06E04",
        chain_slug="ethereum",
    )

    # Multisig governance — expect owner-is-multisig, score ~10
    await test_contract(
        label="Railgun Smart Wallet",
        address="0xfa7093cdd9ee6932b4eb2c9e1cde7ce00b1fa4b9",
        chain_slug="ethereum",
    )

    # Renounced — Uniswap V3 Factory owner() returns address(0)
    await test_contract(
        label="Uniswap V3 Factory (renounced)",
        address="0x1F98431c8aD98523631AE4a59f267346ea31F984",
        chain_slug="ethereum",
    )


if __name__ == "__main__":
    asyncio.run(main())
