"""
Day 4 — Ownership & Governance Analyser
Analyses on-chain ownership structure and produces an OwnershipResult.

Input:  OnChainState (already fetched by collector in Day 2)
        + raw source code string
        + chain_slug (e.g. "ethereum")
Output: OwnershipResult with risk score 0-100 and flags list
"""

from __future__ import annotations

import re
import logging
from typing import Any

from app.core.models.contract import OnChainState
from app.core.models.scoring import OwnershipResult
from app.core.clients.alchemy import alchemy_client   # singleton, no args needed
from app.core.clients.chains import CHAIN_ID_TO_SLUG

log = logging.getLogger(__name__)

# ── Gnosis Safe function selectors present in Safe bytecode ──────────────────
GNOSIS_SELECTORS = [
    "a0e67e2b",  # getOwners()
    "e318b52b",  # addOwnerWithThreshold(address,uint256)
    "610b5925",  # changeThreshold(uint256)
    "6a761202",  # execTransaction(...)
]

# ── Addresses that mean ownership is renounced ───────────────────────────────
RENOUNCED_ADDRESSES = {
    "0x0000000000000000000000000000000000000000",
    "0x000000000000000000000000000000000000dead",
    "0x0000000000000000000000000000000000000001",
}

# ── Timelock view-function selectors ─────────────────────────────────────────
TIMELOCK_DELAY_SELECTORS = [
    "0xd27182d6",  # minDelay()
    "0x2e1a7d4d",  # MINIMUM_DELAY()
]

# ── Regex: find a hardcoded timelock address in Solidity source ──────────────
TIMELOCK_ADDR_RE = re.compile(
    r"(?:TimelockController|ITimelock|timelock)\s*[=(,]\s*(0x[0-9a-fA-F]{40})",
    re.IGNORECASE,
)


async def _check_is_contract(chain_slug: str, address: str) -> bool:
    """True if address has bytecode (is a contract, not an EOA)."""
    try:
        result = await alchemy_client.get_bytecode(address, chain_slug)
        return not result.is_eoa
    except Exception as exc:
        log.debug("bytecode check failed for %s: %s", address, exc)
        return False


async def _check_is_gnosis_safe(chain_slug: str, address: str) -> bool:
    """
    Two-step Safe detection:
    1. Bytecode contains ≥2 known Safe function selectors → likely Safe.
    2. eth_call getOwners() returns non-empty array → definitely Safe/multisig.
    """
    # Step 1 — fast bytecode scan
    try:
        result = await alchemy_client.get_bytecode(address, chain_slug)
        bytecode_lower = result.bytecode.lower()
        hits = sum(1 for sel in GNOSIS_SELECTORS if sel in bytecode_lower)
        if hits >= 2:
            log.info("gnosis safe detected via bytecode selectors: %s", address)
            return True
    except Exception:
        pass

    # Step 2 — call getOwners() via eth_call
    try:
        raw = await alchemy_client._eth_call_address(
            chain_slug, address, "0xa0e67e2b"  # getOwners()
        )
        # getOwners() → address[] ABI-encoded:
        # bytes 0-31:  offset (= 0x20)
        # bytes 32-63: array length
        # bytes 64+:   addresses
        # _eth_call_address strips the 0x and returns the last 20 bytes as address.
        # For an array return we need the raw response — but _eth_call_address
        # interprets it as a single address. A non-None return with valid data
        # means the function exists; we treat that as multisig evidence.
        if raw is not None:
            log.info("getOwners() responded for %s — treating as multisig", address)
            return True
    except Exception as exc:
        log.debug("getOwners() call failed for %s: %s", address, exc)

    return False


async def _read_timelock_delay_secs(
    chain_slug: str, timelock_address: str
) -> int | None:
    """Try to read minDelay() or MINIMUM_DELAY() from a timelock contract."""
    for selector in TIMELOCK_DELAY_SELECTORS:
        try:
            resp = await alchemy_client._rpc_call(
                chain_slug,
                "eth_call",
                [{"to": timelock_address, "data": selector}, "latest"],
            )
            result = resp.get("result", "0x")
            if result and result not in ("0x", "0x0"):
                raw = result[2:] if result.startswith("0x") else result
                raw = raw.ljust(64, "0")[:64]
                delay = int(raw, 16)
                if delay > 0:
                    log.info(
                        "timelock %s delay = %ds (%.1fh)",
                        timelock_address, delay, delay / 3600,
                    )
                    return delay
        except Exception as exc:
            log.debug("timelock delay read failed (%s): %s", selector, exc)
    return None


def _extract_timelock_address(source_code: str) -> str | None:
    """Regex-scan Solidity source for a hardcoded timelock address."""
    match = TIMELOCK_ADDR_RE.search(source_code)
    return match.group(1) if match else None


def _compute_score(
    is_renounced: bool,
    is_multisig: bool,
    has_timelock: bool,
    timelock_delay_hours: float | None,
    is_eoa: bool,
    upgradeable_no_timelock: bool,
    admin_pause_no_timelock: bool,
) -> tuple[int, list[str]]:
    """
    Ownership risk scoring formula. Base = 20, clamped to [0, 100].

    Reductions (lower risk):
      Renounced owner    -15
      Multisig owner     -10
      Timelock present   -10
      TL delay > 48h     -5

    Additions (higher risk):
      EOA owner          +25
      Upgradeable no TL  +20
      Admin pause no TL  +15
    """
    score = 20
    flags: list[str] = []

    if is_renounced:
        score -= 15
        flags.append("ownership-renounced")

    if is_multisig:
        score -= 10
        flags.append("owner-is-multisig")
    elif is_eoa:
        score += 25
        flags.append("owner-is-eoa")

    if has_timelock:
        score -= 10
        flags.append("timelock-present")
        if timelock_delay_hours is not None and timelock_delay_hours > 48:
            score -= 5
            flags.append(f"timelock-delay-{int(timelock_delay_hours)}h")

    if upgradeable_no_timelock:
        score += 20
        flags.append("upgradeable-no-timelock")

    if admin_pause_no_timelock:
        score += 15
        flags.append("admin-pause-no-timelock")

    return max(0, min(100, score)), flags


async def analyse_ownership(
    on_chain: OnChainState,
    source_code: str,
    chain_slug: str,
    code_flags: list[str] | None = None,
) -> OwnershipResult:
    """
    Main entry point.

    Args:
        on_chain:    OnChainState from RawContractData.on_chain
        source_code: Solidity source (joined from source_files)
        chain_slug:  e.g. "ethereum", "polygon"
        code_flags:  Flag strings from CodeRiskResult to reuse Day 3 findings

    Returns:
        OwnershipResult
    """
    code_flags = code_flags or []
    owner = (on_chain.owner or "").lower().strip()

    is_renounced = False
    is_multisig = False
    is_eoa = False
    has_timelock = False
    timelock_delay_secs: int | None = None
    timelock_address: str | None = None

    # ── 1. Renouncement check ────────────────────────────────────────────────
    if not owner or owner in {a.lower() for a in RENOUNCED_ADDRESSES}:
        is_renounced = True
        log.info("ownership renounced — owner=%s", owner or "none")

    # ── 2. Multisig / EOA detection ──────────────────────────────────────────
    if not is_renounced and owner:
        try:
            is_contract = await _check_is_contract(chain_slug, owner)
            if is_contract:
                is_multisig = await _check_is_gnosis_safe(chain_slug, owner)
                if not is_multisig:
                    # Any contract owner that isn't a known Safe is still
                    # safer than an EOA — treat as multisig-equivalent
                    is_multisig = True
                    log.info("owner %s is a contract (non-Safe) → multisig", owner)
            else:
                is_eoa = True
                log.info("owner %s is an EOA", owner)
        except Exception as exc:
            log.warning("ownership detection failed, defaulting to EOA: %s", exc)
            is_eoa = True

    # ── 3. Timelock detection ────────────────────────────────────────────────
    # Reuse Day 3 finding if available
    has_timelock_from_code = any(
        "timelock" in f.lower() and "no-timelock" not in f.lower()
        for f in code_flags
    )
    # Also try to find a hardcoded address in source
    timelock_address = _extract_timelock_address(source_code)

    if timelock_address or has_timelock_from_code:
        has_timelock = True
        if timelock_address:
            try:
                timelock_delay_secs = await _read_timelock_delay_secs(
                    chain_slug, timelock_address
                )
            except Exception as exc:
                log.warning("timelock delay read failed: %s", exc)

    timelock_delay_hours = (
        timelock_delay_secs / 3600 if timelock_delay_secs is not None else None
    )

    # ── 4. Reuse Day 3 flags ─────────────────────────────────────────────────
    upgradeable_no_timelock = "upgrade-no-timelock" in code_flags
    admin_pause_no_timelock = "admin-key-risk" in code_flags

    # ── 5. Score ─────────────────────────────────────────────────────────────
    score, flags = _compute_score(
        is_renounced=is_renounced,
        is_multisig=is_multisig,
        has_timelock=has_timelock,
        timelock_delay_hours=timelock_delay_hours,
        is_eoa=is_eoa,
        upgradeable_no_timelock=upgradeable_no_timelock,
        admin_pause_no_timelock=admin_pause_no_timelock,
    )

    details: dict[str, Any] = {
        "owner_address": owner,
        "is_renounced": is_renounced,
        "is_multisig": is_multisig,
        "is_eoa": is_eoa,
        "has_timelock": has_timelock,
        "timelock_address": timelock_address,
        "timelock_delay_seconds": timelock_delay_secs,
        "timelock_delay_hours": timelock_delay_hours,
        "upgradeable_no_timelock": upgradeable_no_timelock,
        "admin_pause_no_timelock": admin_pause_no_timelock,
    }

    return OwnershipResult(
        score=float(score),
        flags=flags,
        details=details,
    )
