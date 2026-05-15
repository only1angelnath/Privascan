"""
Day 9 — Audit Quality Analyser
Queries audit_records table and returns a 0-100 risk score.
Higher score = more risk (less/worse audit coverage).

Formula:
  Base score: 80 (no audits on record)
  Per audit:
    Tier 1 auditor (Trail of Bits, OZ, Certik, Spearbit, Sigma Prime): -30
    Tier 2 auditor:                                                       -20
    Tier 3 auditor:                                                       -10
    Formal verification:                                                  -10 (additional)
  Per unresolved critical finding:                                        +25
  Per unresolved high finding:                                            +15
  All criticals resolved (and >0 criticals found):                         -5
  Clamped to [0, 100]
"""

from __future__ import annotations

import logging
from app.db.session import get_sync_session
from app.db.models import AuditRecord

log = logging.getLogger(__name__)

# Score deductions per audit tier
TIER_DEDUCTIONS = {1: 30, 2: 20, 3: 10}

# Score if no audit records found in DB for this protocol
NO_AUDIT_SCORE = 80.0


def analyse_audit(protocol_id: str | None) -> float:
    """
    Compute audit quality risk score for a protocol.

    Args:
        protocol_id: UUID string from protocols table.
                     None → community scan with no protocol → return NO_AUDIT_SCORE.

    Returns:
        float 0-100 (higher = more audit risk)
    """
    if not protocol_id:
        log.info("audit_analyser.no_protocol_id — returning %.1f", NO_AUDIT_SCORE)
        return NO_AUDIT_SCORE

    try:
        with get_sync_session() as db:
            records: list[AuditRecord] = (
                db.query(AuditRecord)
                .filter(AuditRecord.protocol_id == protocol_id)
                .all()
            )
    except Exception as exc:
        log.warning("audit_analyser.db_error protocol=%s: %s", protocol_id, exc)
        return NO_AUDIT_SCORE

    if not records:
        log.info("audit_analyser.no_records protocol=%s — score %.1f", protocol_id, NO_AUDIT_SCORE)
        return NO_AUDIT_SCORE

    score = NO_AUDIT_SCORE
    total_criticals = 0
    total_criticals_resolved = True  # assume resolved unless a record says otherwise

    for record in records:
        # ── Tier deduction ────────────────────────────────────────────────────
        tier = record.auditor_tier or 3
        deduction = TIER_DEDUCTIONS.get(tier, 10)
        score -= deduction

        # ── Formal verification bonus ─────────────────────────────────────────
        if record.is_formal_verification:
            score -= 10

        # ── Unresolved critical findings penalty ──────────────────────────────
        crits = record.critical_findings or 0
        total_criticals += crits
        if crits > 0:
            if not record.critical_resolved:
                score += 25 * crits
                total_criticals_resolved = False
            # else: criticals exist but all resolved — handled below

        # ── Unresolved high findings penalty ─────────────────────────────────
        highs = record.high_findings or 0
        # We don't have a high_resolved column — use presence as indicator.
        # Tier 1 audits with highs assume they're tracked; we penalise once per record.
        # A more granular model can be added Day 13.
        if highs > 0 and not record.critical_resolved:
            # If critical_resolved is False, high findings likely also unresolved
            score += 15 * highs

    # ── All criticals resolved bonus (applied once if any crits found + all resolved) ──
    if total_criticals > 0 and total_criticals_resolved:
        score -= 5

    final = max(0.0, min(100.0, round(score, 2)))
    log.info(
        "audit_analyser.scored protocol=%s audits=%d score=%.1f",
        protocol_id, len(records), final,
    )
    return final
