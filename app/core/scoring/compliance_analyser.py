"""
Day 9 — Compliance Risk Analyser
Queries ofac_addresses + exploit_records tables for a contract address.
Returns a 0-100 sub-score that feeds the 0.08×compliance weight in
the composite formula.

This is SEPARATE from the override engine (engine.py) which hard-caps
the total composite score. This sub-score just contributes to the formula.

Score:
  No issues:                      0
  OFAC sanctioned (active):     100
  Unresolved exploit:             80
  Resolved exploit:               30
  Previously OFAC (delisted):     20
"""

from __future__ import annotations

import logging
from app.db.session import get_sync_session
from app.db.models import OfacAddress, ExploitRecord

log = logging.getLogger(__name__)


def analyse_compliance(address: str) -> float:
    """
    Compute compliance risk sub-score for a contract address.

    Args:
        address: EVM contract address (0x...)

    Returns:
        float 0-100 (higher = more compliance risk)
    """
    addr = address.lower().strip()
    score = 0.0

    try:
        with get_sync_session() as db:
            # ── OFAC check ────────────────────────────────────────────────────
            ofac_row: OfacAddress | None = (
                db.query(OfacAddress)
                .filter(OfacAddress.address == addr)
                .first()
            )

            if ofac_row is not None:
                if not ofac_row.was_delisted:
                    # Active OFAC sanction — maximum compliance risk
                    log.info("compliance.ofac_active address=%s", addr)
                    return 100.0
                else:
                    # Previously sanctioned but delisted — still elevated
                    score = max(score, 20.0)
                    log.info("compliance.ofac_delisted address=%s score=20", addr)

            # ── Exploit check ─────────────────────────────────────────────────
            exploits: list[ExploitRecord] = (
                db.query(ExploitRecord)
                .filter(ExploitRecord.contract_address == addr)
                .all()
            )

            for exploit in exploits:
                if not exploit.is_resolved:
                    score = max(score, 80.0)
                    log.info(
                        "compliance.exploit_unresolved address=%s loss_usd=%s",
                        addr, exploit.loss_usd,
                    )
                else:
                    score = max(score, 30.0)
                    log.info("compliance.exploit_resolved address=%s", addr)

    except Exception as exc:
        log.warning("compliance_analyser.db_error address=%s: %s", addr, exc)
        # Return neutral on DB error — don't penalise unfairly
        return 0.0

    final = round(score, 2)
    log.info("compliance_analyser.scored address=%s score=%.1f", addr, final)
    return final
