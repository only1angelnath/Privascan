"""
Day 7 — Score Aggregator  (updated Day 9: audit + compliance wired)
Takes sub-scores from all analysers → weighted composite → grade → overrides.

Composite formula (from system design):
  composite = 0.30×code + 0.25×ownership + 0.20×liquidity
            + 0.12×audit + 0.08×compliance + 0.05×governance

Grade scale (higher score = more risk):
  A  0–20   Low Risk
  B  21–40  Moderate-Low Risk
  C  41–60  Moderate Risk
  D  61–80  High Risk
  F  81–100 Critical Risk

Override rules (hard caps — applied by engine.py AFTER aggregation):
  OFAC active       → score capped at 10, grade F
  Exploit active    → score capped at 30, grade F
"""

from __future__ import annotations
import logging
from datetime import datetime

log = logging.getLogger(__name__)

# ── Composite weights ─────────────────────────────────────────────────────────
WEIGHTS = {
    "code":        0.30,
    "ownership":   0.25,
    "liquidity":   0.20,
    "audit":       0.12,
    "compliance":  0.08,
    "governance":  0.05,
}

# ── Grade thresholds (score = risk, so lower = safer) ────────────────────────
GRADE_THRESHOLDS = [
    (20,  "A"),
    (40,  "B"),
    (60,  "C"),
    (80,  "D"),
    (100, "F"),
]


def _grade(score: float) -> str:
    for threshold, letter in GRADE_THRESHOLDS:
        if score <= threshold:
            return letter
    return "F"


def _check_overrides(
    composite: float,
    address: str,
    ofac_active: bool = False,
    exploit_active: bool = False,
) -> tuple[float, str | None, str]:
    """
    Apply hard override rules.
    Returns (final_score, override_status, grade).
    """
    if ofac_active:
        return 10.0, "ofac_active", "F"
    if exploit_active:
        capped = min(composite, 30.0)
        return capped, "exploit_active", "F"
    return composite, None, _grade(composite)


def aggregate(
    code_score: float,
    ownership_score: float,
    liquidity_score: float,
    audit_score: float = 50.0,
    compliance_score: float = 50.0,
    governance_score: float = 50.0,
    ofac_active: bool = False,
    exploit_active: bool = False,
    address: str = "",
) -> dict:
    """
    Compute weighted composite score and grade.

    audit_score and compliance_score should be pre-computed by the caller
    using audit_analyser.analyse_audit() and compliance_analyser.analyse_compliance().
    They still default to 50.0 (neutral) if not supplied.

    governance_score remains 50.0 (neutral) until Day 9 governance analyser.
    """
    raw_composite = (
        code_score       * WEIGHTS["code"]        +
        ownership_score  * WEIGHTS["ownership"]   +
        liquidity_score  * WEIGHTS["liquidity"]   +
        audit_score      * WEIGHTS["audit"]       +
        compliance_score * WEIGHTS["compliance"]  +
        governance_score * WEIGHTS["governance"]
    )
    raw_composite = round(max(0.0, min(100.0, raw_composite)), 2)

    final_score, override_status, grade = _check_overrides(
        raw_composite, address, ofac_active, exploit_active
    )

    log.info(
        "aggregator.scored address=%s composite=%.1f grade=%s override=%s "
        "audit=%.1f compliance=%.1f",
        address, final_score, grade, override_status, audit_score, compliance_score,
    )

    return {
        "composite_score": round(final_score, 2),
        "grade": grade,
        "override_applied": override_status is not None,
        "override_status": override_status,
        "sub_scores": {
            "code":        round(code_score, 2),
            "ownership":   round(ownership_score, 2),
            "liquidity":   round(liquidity_score, 2),
            "audit":       round(audit_score, 2),
            "compliance":  round(compliance_score, 2),
            "governance":  round(governance_score, 2),
        },
        "scored_at": datetime.utcnow().isoformat(),
    }


def score_to_label(score: float) -> str:
    """Human-readable risk label for the grade."""
    labels = {
        "A": "Low Risk",
        "B": "Moderate-Low Risk",
        "C": "Moderate Risk",
        "D": "High Risk",
        "F": "Critical Risk",
    }
    return labels.get(_grade(score), "Unknown")
