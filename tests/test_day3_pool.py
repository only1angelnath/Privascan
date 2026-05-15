"""
Day 3 test — privacy detectors on real privacy pool contracts.
Tests both Tornado Cash (expected clean) and a less audited pool.
"""

import asyncio
from app.core.clients.collector import collect_contract_data
from app.core.scoring.code_analyser import analyse_contract, get_code_risk_recommendations
from app.core.detectors.privacy_detectors import run_all_privacy_detectors


async def test_contract(address: str, chain: str, name: str, scan_type: str = "community"):
    print(f"\n── {name} ──────────────────────────────────────")
    print(f"  Address : {address}")

    raw = await collect_contract_data(
        address=address,
        chain_slug=chain,
        scan_type=scan_type,
    )

    if not raw.source or not raw.source.is_verified:
        print(f"  ✗ Not verified — skipping Slither")
        print(f"  code_risk_score : 60.0 (unverified penalty)")
        return

    print(f"  contract_name   : {raw.source.contract_name}")
    print(f"  compiler        : {raw.source.compiler_version}")
    print(f"  is_proxy        : {raw.source.is_proxy}")
    print(f"  Running Slither + privacy detectors...")

    result = await analyse_contract(raw)

    print(f"  code_risk_score : {result.score}")
    print(f"  analysis_time   : {result.analysis_duration_seconds:.1f}s")
    print(f"  total_findings  : {len(result.findings)}")
    print(f"  high            : {result.high_count}")
    print(f"  medium          : {result.medium_count}")
    print(f"  low             : {result.low_count}")

    if result.findings:
        print(f"\n  Findings:")
        for f in result.findings:
            tag = "[CUSTOM]" if f.is_custom else "[SLITHER]"
            print(f"    {tag} [{f.impact}/{f.confidence}] {f.check}")
            print(f"           {f.description[:120].strip()}")

    recs = get_code_risk_recommendations(result)
    if recs:
        print(f"\n  Recommendations:")
        for r in recs:
            print(f"    • {r}")


async def main():
    print("\n══ Day 3 Privacy Pool Detector Tests ══════════════")

    # 1. Tornado Cash 100 ETH pool — well audited, expect clean
    await test_contract(
        address="0x910Cbd523D972eb0a6f4cAe4618aD62622b39DbF",
        chain="ethereum",
        name="Tornado Cash 100 ETH Pool",
    )

    # 2. Tornado Cash 100k DAI pool — already tested, expect clean
    await test_contract(
        address="0x23773e65ed146a459791799d01336db287f25334",
        chain="ethereum",
        name="Tornado Cash 100k DAI Pool",
    )

    # 3. Umbra Privacy Protocol — stealth address protocol on Ethereum
    await test_contract(
        address="0xFb2dc580Eed955B528407b4d36FfaFe3da685401",
        chain="ethereum",
        name="Umbra Stealth Address Protocol",
    )

    print("\n══ All tests complete ✓ ════════════════════════════\n")


if __name__ == "__main__":
    asyncio.run(main())
