"""
Day 3 test — Tornado Cash 100,000 DAI Pool
Real privacy pool with nullifiers, verifier, withdraw function.
Expected to trigger privacy-specific detectors.
"""

import asyncio
from app.core.clients.collector import collect_contract_data
from app.core.scoring.code_analyser import analyse_contract, get_code_risk_recommendations

# Tornado Cash 100k DAI pool — verified, real mixer contract
TEST_ADDRESS = "0x23773e65ed146a459791799d01336db287f25334"
TEST_CHAIN = "ethereum"

async def main():
    print("\n── Day 3 Privacy Pool Test — Tornado Cash 100k DAI ──")
    print(f"Address  : {TEST_ADDRESS}")
    print(f"Chain    : {TEST_CHAIN}")
    print("──────────────────────────────────────────────────────\n")

    print("Step 1: Collecting contract data...")
    raw = await collect_contract_data(
        address=TEST_ADDRESS,
        chain_slug=TEST_CHAIN,
        scan_type="community",
    )
    print(f"  verified      : {raw.source.is_verified if raw.source else False}")
    print(f"  contract_name : {raw.source.contract_name if raw.source else 'N/A'}")
    print(f"  compiler      : {raw.source.compiler_version if raw.source else 'N/A'}")
    print(f"  is_proxy      : {raw.source.is_proxy if raw.source else 'N/A'}")

    print("\nStep 2: Running Slither + privacy detectors...")
    print("  (30-90 seconds for complex contracts)\n")

    result = await analyse_contract(raw)

    print("── Results ────────────────────────────────────────────")
    print(f"  code_risk_score : {result.score}")
    print(f"  analysis_time   : {result.analysis_duration_seconds:.1f}s")
    print(f"  slither_error   : {result.error}")
    print(f"  total_findings  : {len(result.findings)}")
    print(f"  critical        : {result.critical_count}")
    print(f"  high            : {result.high_count}")
    print(f"  medium          : {result.medium_count}")
    print(f"  low             : {result.low_count}")

    if result.findings:
        print("\n── Findings ───────────────────────────────────────────")
        for f in result.findings:
            tag = "[CUSTOM]" if f.is_custom else "[SLITHER]"
            amp = f"amp={f.amplifier}" if f.is_custom else ""
            print(f"  {tag} [{f.impact}/{f.confidence}] {f.check} {amp}")
            print(f"         {f.description[:150].strip()}")
            print()

    recs = get_code_risk_recommendations(result)
    if recs:
        print("── Recommendations ────────────────────────────────────")
        for i, r in enumerate(recs, 1):
            print(f"  {i}. {r}")

    print("\n──────────────────────────────────────────────────────")
    print("Test complete ✓\n")


if __name__ == "__main__":
    asyncio.run(main())
