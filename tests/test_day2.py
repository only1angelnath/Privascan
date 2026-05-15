"""
Day 2 community scan test — Panther Protocol
ZK privacy protocol, community scan path, TVL via Dune SIM.
"""

import asyncio
from app.core.clients.collector import collect_contract_data

# Panther Protocol ZKP Token contract on Ethereum
TEST_ADDRESS = "0xfb78e37b93b16b9ab4256e27ab6b32b98e6fdb97"
TEST_CHAIN = "base"

async def main():
    print("\n── Community Scan Test (Dune SIM TVL) ────────────")
    print(f"Protocol : PRXVT AI Deposit on Base (PRXVT)")
    print(f"Address  : {TEST_ADDRESS}")
    print(f"Chain    : {TEST_CHAIN}")
    print(f"Scan type: community (no DefiLlama slug)")
    print("──────────────────────────────────────────────────\n")

    data = await collect_contract_data(
        address=TEST_ADDRESS,
        chain_slug=TEST_CHAIN,
        protocol_defillama_slug=None,   # not on DefiLlama — use Dune SIM
        scan_type="community",
    )

    print("── Source Code ────────────────────────────────────")
    if data.source:
        print(f"  verified      : {data.source.is_verified}")
        print(f"  contract_name : {data.source.contract_name}")
        print(f"  compiler      : {data.source.compiler_version}")
        print(f"  is_proxy      : {data.source.is_proxy}")
    else:
        print("  ✗ fetch failed")

    print("\n── Deployment ─────────────────────────────────────")
    if data.creation:
        print(f"  creator       : {data.creation.creator_address}")
        print(f"  creation_tx   : {data.creation.creation_tx_hash}")
    else:
        print("  ✗ fetch failed")

    print("\n── Bytecode ───────────────────────────────────────")
    if data.bytecode:
        print(f"  is_eoa        : {data.bytecode.is_eoa}")
        print(f"  bytecode_len  : {len(data.bytecode.bytecode)} chars")
    else:
        print("  ✗ fetch failed")

    print("\n── On-Chain State ─────────────────────────────────")
    if data.on_chain:
        print(f"  owner         : {data.on_chain.owner}")
        print(f"  admin         : {data.on_chain.admin}")
        print(f"  is_paused     : {data.on_chain.is_paused}")
        print(f"  eth_balance   : {data.on_chain.eth_balance_wei} wei")
    else:
        print("  ✗ fetch failed")

    print("\n── TVL (Dune SIM) ─────────────────────────────────")
    if data.tvl:
        print(f"  tvl_usd       : ${data.tvl.tvl_usd:,.2f}" if data.tvl.tvl_usd else "  tvl_usd       : None (no qualifying assets)")
        print(f"  source        : {data.tvl.source}")
        print(f"  confidence    : {data.tvl.confidence}")
    else:
        print("  ✗ fetch failed")

    print("\n──────────────────────────────────────────────────")
    print("Community scan test complete ✓\n")


if __name__ == "__main__":
    asyncio.run(main())
