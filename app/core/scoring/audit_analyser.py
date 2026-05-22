"""
Audit Quality Analyser — Day 15 rewrite.

Score range: [0, 100] — lower = less risk (better audit coverage).

Model:
  - No audits → 80 (significant risk)
  - Audits blended via diminishing-returns weighted average (first audit dominates)
  - Tier 1 (ToB, OZ, Consensys, Halborn)    → target score 15
  - Tier 2 (Quantstamp, PeckShield, CertiK) → target score 30
  - Tier 3 (all others)                      → target score 50
  - Stale audits (>24 months): effective score halfway between tier target and 80
  - Formal verification bonus: −10
  - Unresolved critical findings: +25 each
  - Unresolved high findings: +10 each
  - All criticals resolved bonus: −5 (applied once)
  - Final clamped to [0, 100]
"""
from __future__ import annotations
import logging
from datetime import date

log = logging.getLogger(__name__)

NO_AUDIT_SCORE = 80.0
TIER_BASE: dict[int, float] = {1: 15.0, 2: 30.0, 3: 50.0}
STALE_MONTHS = 24


def analyse_audit(protocol_id: str | None) -> float:
    """Return audit risk score [0,100]. Lower = less risk."""
    if not protocol_id:
        log.info("audit_analyser.no_protocol_id — score %.1f", NO_AUDIT_SCORE)
        return NO_AUDIT_SCORE

    try:
        from app.db.session import get_sync_session
        from app.db.models import AuditRecord
    except ImportError as exc:
        log.warning("audit_analyser.import_error: %s", exc)
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
        log.info("audit_analyser.no_records protocol=%s — score %.1f",
                 protocol_id, NO_AUDIT_SCORE)
        return NO_AUDIT_SCORE

    today = date.today()

    # ── Step 1: weighted blend — best tier first, diminishing returns ─────────
    sorted_records = sorted(records, key=lambda r: (r.auditor_tier or 3))
    total_weight   = 0.0
    weighted_score = 0.0
    weight         = 1.0   # each subsequent audit contributes 40% of the previous

    for record in sorted_records:
        tier      = record.auditor_tier or 3
        tier_base = TIER_BASE.get(tier, 50.0)
        if record.audit_date:
            months_old = (today - record.audit_date).days / 30
            effective  = tier_base if months_old <= STALE_MONTHS \
                         else (tier_base + NO_AUDIT_SCORE) / 2
        else:
            effective = tier_base
        weighted_score += effective * weight
        total_weight   += weight
        weight         *= 0.4

    score = weighted_score / total_weight

    # ── Step 2: formal verification bonus ─────────────────────────────────────
    if any(getattr(r, 'is_formal_verification', False) for r in records):
        score -= 10.0

    # ── Step 3: unresolved findings penalties ─────────────────────────────────
    total_criticals          = 0
    total_criticals_resolved = True

    for record in records:
        crits = record.critical_findings or 0
        total_criticals += crits
        if crits > 0 and not record.critical_resolved:
            score                  += 25 * crits
            total_criticals_resolved = False
        highs = record.high_findings or 0
        if highs > 0 and not record.critical_resolved:
            score += 10 * highs

    # ── Step 4: all-criticals-resolved bonus ──────────────────────────────────
    if total_criticals > 0 and total_criticals_resolved:
        score -= 5.0

    final = max(0.0, min(100.0, round(score, 2)))
    log.info("audit_analyser.scored protocol=%s audits=%d score=%.1f",
             protocol_id, len(records), final)
    return final
