"""
Day 5 — Liquidity / TVL Analyser
Pure math — no RPC calls. TvlResult already fetched by collector (Day 2).

Input:  TvlResult from RawContractData.tvl
Output: LiquidityResult with risk score 0-100 and tier label
"""

from __future__ import annotations

import logging
from app.core.models.contract import TvlResult
from app.core.models.scoring import LiquidityResult

log = logging.getLogger(__name__)

# ── TVL tier thresholds (USD) ─────────────────────────────────────────────────
# Higher TVL = more established = lower risk score
TVL_TIERS: list[tuple[float, str, int]] = [
    (50_000_000, "whale",   5),
    (10_000_000, "large",  15),
     (1_000_000, "medium", 30),
       (100_000, "small",  50),
             (0, "minimal", 70),
]
TVL_TIER_NONE = ("none", 90)   # no TVL data at all


def _get_tier(tvl_usd: float) -> tuple[str, int]:
    """Map a TVL value to (tier_name, base_score)."""
    for threshold, tier, score in TVL_TIERS:
        if tvl_usd > threshold:
            return tier, score
    return TVL_TIER_NONE


def _apply_confidence(base_score: int, confidence: str) -> float:
    """
    Blend the base score toward neutral (50) based on data confidence.

    high   → score unchanged        (we trust the data)
    medium → 80% score + 20% of 50  (slight pull toward neutral)
    low    → 60% score + 40% of 50  (stronger pull toward neutral)
    none   → fixed 75               (unknown TVL is risky but not worst-case)
    """
    NEUTRAL = 50.0
    if confidence == "high":
        return float(base_score)
    elif confidence == "medium":
        return base_score * 0.80 + NEUTRAL * 0.20
    elif confidence == "low":
        return base_score * 0.60 + NEUTRAL * 0.40
    else:
        # "none" confidence — we have no reliable TVL data
        return 75.0


def analyse_liquidity(
    tvl: TvlResult | None,
    address: str,
    chain_id: int,
) -> LiquidityResult:
    """
    Main entry point — synchronous (pure math, no I/O).

    Args:
        tvl:      TvlResult from RawContractData.tvl (may be None)
        address:  Contract address (for the result model)
        chain_id: Chain ID (for the result model)

    Returns:
        LiquidityResult with score, tier, and source metadata
    """
    # ── No TVL data at all ────────────────────────────────────────────────────
    if tvl is None or tvl.tvl_usd is None:
        log.info(
            "liquidity.no_data address=%s — defaulting to score 90",
            address,
        )
        return LiquidityResult(
            address=address,
            chain_id=chain_id,
            score=90.0,
            tvl_usd=None,
            tvl_source=getattr(tvl, "source", "none") if tvl else "none",
            tvl_confidence=getattr(tvl, "confidence", "none") if tvl else "none",
            tvl_tier="none",
        )

    tvl_usd = tvl.tvl_usd
    confidence = tvl.confidence   # "high" | "medium" | "low" | "none"
    source = tvl.source           # "defillama" | "dune_sim" | "none"

    # ── Tier lookup ───────────────────────────────────────────────────────────
    tier, base_score = _get_tier(tvl_usd)

    # ── Confidence adjustment ─────────────────────────────────────────────────
    final_score = _apply_confidence(base_score, confidence)
    final_score = max(0.0, min(100.0, final_score))

    log.info(
        "liquidity.scored address=%s tvl=$%.0f tier=%s "
        "base=%d confidence=%s final=%.1f",
        address, tvl_usd, tier, base_score, confidence, final_score,
    )

    return LiquidityResult(
        address=address,
        chain_id=chain_id,
        score=round(final_score, 2),
        tvl_usd=tvl_usd,
        tvl_source=source,
        tvl_confidence=confidence,
        tvl_tier=tier,
    )
