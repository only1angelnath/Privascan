"""Override engine — hard score caps for OFAC and exploit flags."""
from __future__ import annotations
import logging
from app.core.overrides.ofac import is_ofac_sanctioned
from app.core.overrides.exploits import get_active_exploit

log = logging.getLogger(__name__)
OFAC_SCORE_CAP    = 10.0
EXPLOIT_SCORE_CAP = 30.0


async def apply_overrides(address: str, score_result: dict) -> dict:
    ofac_hit    = await is_ofac_sanctioned(address)
    exploit_hit = await get_active_exploit(address)
    override_applied = False
    override_status  = None
    override_detail  = None
    if ofac_hit:
        original = score_result["composite_score"]
        score_result["composite_score"] = OFAC_SCORE_CAP
        score_result["grade"]       = "F"
        score_result["grade_label"] = "Critical Risk"
        override_applied = True
        override_status  = "ofac_active"
        override_detail  = {
            "type": "ofac", "cap": OFAC_SCORE_CAP, "original_score": original,
            "message": "Address appears on OFAC SDN or Consolidated sanctions list.",
        }
        log.warning("override.ofac_active address=%s original=%.1f", address, original)
    elif exploit_hit:
        original = score_result["composite_score"]
        capped   = min(original, EXPLOIT_SCORE_CAP)
        score_result["composite_score"] = capped
        score_result["grade"]       = "F"
        score_result["grade_label"] = "Critical Risk"
        override_applied = True
        override_status  = "exploit_active"
        override_detail  = {
            "type": "exploit", "cap": EXPLOIT_SCORE_CAP, "original_score": original,
            "protocol": exploit_hit.get("protocol_name"),
            "loss_usd": exploit_hit.get("loss_usd"),
            "exploit_date": exploit_hit.get("exploit_date"),
            "message": exploit_hit.get("description", "Unresolved exploit on record."),
        }
        log.warning("override.exploit_active address=%s capped=%.1f", address, capped)
    score_result["override_applied"] = override_applied
    score_result["override_status"]  = override_status
    score_result["override_detail"]  = override_detail
    return score_result
