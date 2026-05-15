"""
Day 6 smoke test — calls _run_single_contract_score directly
(the same function score_contract task uses internally).
Verifies the full 3-analyser pipeline works end-to-end.
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# Import the internal helper directly — no Celery broker needed
from app.workers.tasks import _run_single_contract_score


def test(label, address, chain_slug):
    print(f"\n{'='*60}")
    print(f"Testing : {label}")
    print(f"Address : {address}")
    print("="*60)

    result = _run_single_contract_score(
        address=address,
        chain_slug=chain_slug,
        scan_type="community",
    )

    c = result["code"]
    o = result["ownership"]
    l = result["liquidity"]

    print(f"Code score      : {c['score']:.1f}  verified={c['is_verified']}  highs={c['high_count']}")
    print(f"Ownership score : {o['score']:.1f}  flags={o['flags']}")
    print(f"Liquidity score : {l['score']:.1f}  tier={l['tvl_tier']}  tvl=${l['tvl_usd']:,.0f}" if l['tvl_usd'] else f"Liquidity score : {l['score']:.1f}  tier={l['tvl_tier']}  tvl=None")
    print(f"Chain           : {result['chain_slug']}  scan={result['scan_type']}")


if __name__ == "__main__":
    # Railgun — large TVL, multisig owner, clean code
    test(
        "Railgun Smart Wallet",
        "0xfa7093cdd9ee6932b4eb2c9e1cde7ce00b1fa4b9",
        "ethereum",
    )
