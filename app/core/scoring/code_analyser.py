"""
Code risk analyser — orchestrates Slither + privacy detectors.
Public interface: analyse_contract(raw_data) → CodeRiskResult
"""

import structlog
from app.core.models.contract import RawContractData
from app.core.models.scoring import CodeRiskResult, SlitherFinding
from app.core.scoring.slither_runner import run_slither, score_from_findings
from app.core.detectors.privacy_detectors import run_all_privacy_detectors

log = structlog.get_logger()

# Penalty applied when source is not verified — we can't see the code
# so we assume worst case for unverified contracts
UNVERIFIED_PENALTY = 60.0


async def analyse_contract(raw_data: RawContractData) -> CodeRiskResult:
    """
    Run full code risk analysis on a contract.

    Flow:
    1. If not verified → return flat penalty, skip Slither
    2. If verified → run Slither + 5 privacy detectors in sequence
    3. Combine all findings → calculate score
    4. Return CodeRiskResult

    Note: Slither is CPU-bound and synchronous. In production this is
    called from a Celery worker (separate process) so it won't block
    the async event loop. For local testing it runs inline.
    """
    address = raw_data.address
    chain_id = raw_data.chain_id

    # ── Unverified contract — cannot analyse source ────────────────────
    if not raw_data.source or not raw_data.source.is_verified:
        log.info("code_analyser.unverified", address=address)
        return CodeRiskResult(
            address=address,
            chain_id=chain_id,
            score=UNVERIFIED_PENALTY,
            is_verified=False,
            findings=[],
            error="Source code not verified on Etherscan — static analysis skipped",
        )

    source = raw_data.source
    contract_name = source.contract_name or "Contract"
    source_code = source.source_code or ""

    log.info(
        "code_analyser.start",
        address=address,
        contract=contract_name,
        chain=raw_data.chain_slug,
    )

    all_findings: list[SlitherFinding] = []
    slither_error: str | None = None
    duration: float = 0.0

    # ── Run Slither static analysis ────────────────────────────────────
    slither_findings, duration, slither_error = run_slither(
        source_code=source_code,
        contract_name=contract_name,
        compiler_version=source.compiler_version,
    )
    all_findings.extend(slither_findings)

    # ── Run privacy-specific detectors ────────────────────────────────
    privacy_findings = run_all_privacy_detectors(source_code, contract_name)
    all_findings.extend(privacy_findings)

    # ── Calculate score ───────────────────────────────────────────────
    score = score_from_findings(all_findings)

    # If Slither failed entirely, apply partial penalty so the score
    # reflects uncertainty rather than a false zero
    if slither_error and not slither_findings:
        score = max(score, 30.0)

    # Count findings by severity
    critical_count = sum(1 for f in all_findings if f.impact == "Critical")
    high_count     = sum(1 for f in all_findings if f.impact == "High")
    medium_count   = sum(1 for f in all_findings if f.impact == "Medium")
    low_count      = sum(1 for f in all_findings if f.impact == "Low")

    log.info(
        "code_analyser.complete",
        address=address,
        score=score,
        total_findings=len(all_findings),
        high=high_count,
        medium=medium_count,
    )

    return CodeRiskResult(
        address=address,
        chain_id=chain_id,
        score=score,
        is_verified=True,
        findings=all_findings,
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        analysis_duration_seconds=duration,
        error=slither_error,
    )


def get_code_risk_recommendations(result: CodeRiskResult) -> list[str]:
    """
    Generate human-readable recommendations based on findings.
    Called by the composite scorer to populate the recommendations field.
    """
    recommendations = []

    if not result.is_verified:
        recommendations.append(
            "Contract source code is not verified on Etherscan. "
            "Request verification before deploying significant TVL."
        )
        return recommendations

    # Group custom findings by check type
    check_types = {f.check for f in result.findings}

    if "mixer-reentrancy" in check_types:
        recommendations.append(
            "Reentrancy risk in withdrawal path: ensure nullifier/commitment state "
            "is updated BEFORE any external calls (checks-effects-interactions pattern)."
        )

    if "zk-verifier-bypass" in check_types:
        recommendations.append(
            "ZK verifier result must be checked in a require() statement. "
            "Consider making the verifier contract immutable after deployment."
        )

    if "nullifier-reuse" in check_types:
        recommendations.append(
            "Add explicit require(!nullifiers[nullifierHash]) check at the start "
            "of all withdrawal functions before any state changes or external calls."
        )

    if "admin-key-risk" in check_types:
        recommendations.append(
            "Wrap admin functions (pause, blacklist, fee changes) behind a "
            "TimelockController with minimum 48-hour delay."
        )

    if "upgrade-no-timelock" in check_types:
        recommendations.append(
            "Add a TimelockController to the upgrade path. Users of a privacy "
            "protocol need advance notice before logic changes take effect."
        )

    if result.high_count > 0:
        recommendations.append(
            f"{result.high_count} high-severity finding(s) detected by Slither. "
            "Review and remediate before increasing protocol TVL."
        )

    return recommendations
