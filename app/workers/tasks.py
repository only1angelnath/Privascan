"""
Celery tasks — Day 6 wiring.

IMPORTANT: Celery tasks run in separate worker processes (not the async
event loop). All tasks are sync `def`. Async analysers are called via
asyncio.run() inside each task.

Task hierarchy:
  rescore_all_curated
    └── score_ecosystem(protocol_id)   ← one per protocol
          └── score_contract(address)  ← one per contract in ecosystem

  score_contract is also called directly for community (Track B) scans.
"""

import asyncio
import structlog
from celery import group

from app.workers.celery_app import celery_app

log = structlog.get_logger()

# ── Role weights for ecosystem code risk aggregation ──────────────────────────
# Mirrors the system design — pool contracts carry 1.5x weight, tokens 0.8x
ROLE_WEIGHTS: dict[str, float] = {
    "pool":       1.5,
    "verifier":   1.4,
    "vault":      1.3,
    "router":     1.2,
    "proxy":      1.2,
    "governance": 1.0,
    "other":      1.0,
    "token":      0.8,
    "timelock":   0.7,
}


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _run_single_contract_score(
    address: str,
    chain_slug: str,
    protocol_defillama_slug: str | None = None,
    scan_type: str = "community",
    code_flags: list[str] | None = None,
) -> dict:
    """
    Synchronous wrapper that runs all three analysers for one contract.
    Returns a flat dict with all sub-scores — safe to store or return from task.
    """
    from app.core.clients.collector import collect_contract_data
    from app.core.scoring.code_analyser import analyse_contract
    from app.core.scoring.ownership_analyser import analyse_ownership
    from app.core.scoring.liquidity_analyser import analyse_liquidity

    # ── 1. Collect raw data ───────────────────────────────────────────────────
    raw = asyncio.run(
        collect_contract_data(
            address=address,
            chain_slug=chain_slug,
            protocol_defillama_slug=protocol_defillama_slug,
            scan_type=scan_type,
        )
    )

    # ── 2. Code risk (Slither — CPU-bound, runs synchronously inside worker) ──
    code_result = asyncio.run(analyse_contract(raw))

    # ── 3. Ownership (RPC calls via Alchemy) ──────────────────────────────────
    source_code = ""
    if raw.source and raw.source.source_code:
        source_code = raw.source.source_code

    on_chain = raw.on_chain
    ownership_result = None
    if on_chain is not None:
        # Pass code flags so ownership analyser can reuse Day 3 findings
        # without re-running Slither
        all_code_flags = [f.check for f in code_result.findings]
        if code_flags:
            all_code_flags.extend(code_flags)

        ownership_result = asyncio.run(
            analyse_ownership(
                on_chain=on_chain,
                source_code=source_code,
                chain_slug=chain_slug,
                code_flags=all_code_flags,
            )
        )

    # ── 4. Liquidity (pure math — no I/O) ────────────────────────────────────
    liquidity_result = analyse_liquidity(
        tvl=raw.tvl,
        address=address,
        chain_id=raw.chain_id,
    )

    return {
        "address": address,
        "chain_slug": chain_slug,
        "chain_id": raw.chain_id,
        "scan_type": scan_type,
        "code": {
            "score": code_result.score,
            "is_verified": code_result.is_verified,
            "high_count": code_result.high_count,
            "medium_count": code_result.medium_count,
            "flags": [f.check for f in code_result.findings],
            "error": code_result.error,
        },
        "ownership": {
            "score": ownership_result.score if ownership_result else 50.0,
            "flags": ownership_result.flags if ownership_result else [],
            "details": ownership_result.details if ownership_result else {},
        } if ownership_result else {"score": 50.0, "flags": [], "details": {}},
        "liquidity": {
            "score": liquidity_result.score,
            "tvl_usd": liquidity_result.tvl_usd,
            "tvl_tier": liquidity_result.tvl_tier,
            "tvl_source": liquidity_result.tvl_source,
            "tvl_confidence": liquidity_result.tvl_confidence,
        },
    }


def _aggregate_ecosystem_code_risk(
    contract_scores: list[dict],
) -> float:
    """
    Role-weighted average of code risk scores across all ecosystem contracts.
    Contracts with higher-risk roles (pool, verifier) count more.
    """
    if not contract_scores:
        return 0.0

    total_weight = 0.0
    weighted_sum = 0.0

    for c in contract_scores:
        role = c.get("role", "other")
        weight = ROLE_WEIGHTS.get(role, 1.0)
        score = c.get("code_score", 0.0)
        weighted_sum += score * weight
        total_weight += weight

    return weighted_sum / total_weight if total_weight > 0 else 0.0


# ─────────────────────────────────────────────────────────────────────────────
# CELERY TASKS
# ─────────────────────────────────────────────────────────────────────────────

@celery_app.task(
    name="app.workers.tasks.score_contract",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def score_contract(
    self,
    address: str,
    chain_slug: str,
    protocol_defillama_slug: str | None = None,
    scan_type: str = "community",
):
    """
    Score a single contract — used for Track B community scans and
    as a building block for ecosystem scoring.

    Args:
        address:                  EVM contract address
        chain_slug:               e.g. "ethereum", "polygon"
        protocol_defillama_slug:  e.g. "railgun" — for curated TVL via DefiLlama
        scan_type:                "community" | "curated"

    Returns dict with code/ownership/liquidity sub-scores.
    """
    log.info(
        "task.score_contract.start",
        address=address,
        chain=chain_slug,
        scan_type=scan_type,
    )

    try:
        result = _run_single_contract_score(
            address=address,
            chain_slug=chain_slug,
            protocol_defillama_slug=protocol_defillama_slug,
            scan_type=scan_type,
        )
        log.info(
            "task.score_contract.complete",
            address=address,
            code_score=result["code"]["score"],
            ownership_score=result["ownership"]["score"],
            liquidity_score=result["liquidity"]["score"],
        )
        return result

    except Exception as exc:
        log.error("task.score_contract.error", address=address, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.workers.tasks.score_ecosystem",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def score_ecosystem(self, protocol_id: str, scan_type: str = "curated"):
    """
    Score all contracts in a protocol ecosystem.

    Fetches contracts from the DB, scores each one, then:
    - Aggregates code risk using role weights
    - Uses the primary contract for ownership + liquidity
    - Returns the full ecosystem score dict (Day 7 aggregator will
      combine this into a CompositeScore and persist it)

    Args:
        protocol_id: UUID string of the protocol in the DB
        scan_type:   "curated" | "community"
    """
    log.info("task.score_ecosystem.start", protocol_id=protocol_id)

    try:
        # ── Fetch protocol + contracts from DB ────────────────────────────────
        from app.db.session import get_sync_session
        from app.db.models import Protocol, ProtocolContract

        with get_sync_session() as db:
            protocol = db.query(Protocol).filter(
                Protocol.id == protocol_id
            ).first()

            if not protocol:
                log.error("task.score_ecosystem.protocol_not_found", protocol_id=protocol_id)
                return {"error": f"Protocol {protocol_id} not found"}

            contracts = db.query(ProtocolContract).filter(
                ProtocolContract.protocol_id == protocol_id
            ).all()

        if not contracts:
            log.warning("task.score_ecosystem.no_contracts", protocol_id=protocol_id)
            return {"error": "No contracts registered for this protocol"}

        # ── Score each contract ───────────────────────────────────────────────
        from app.core.clients.chains import CHAIN_ID_TO_SLUG

        contract_results = []
        primary_result = None

        for contract in contracts:
            chain_slug = CHAIN_ID_TO_SLUG.get(contract.chain_id, "ethereum")
            try:
                result = _run_single_contract_score(
                    address=contract.address,
                    chain_slug=chain_slug,
                    protocol_defillama_slug=protocol.defillama_slug,
                    scan_type=scan_type,
                )
                result["role"] = contract.contract_role
                result["label"] = contract.label
                result["code_score"] = result["code"]["score"]
                contract_results.append(result)

                if contract.is_primary:
                    primary_result = result

            except Exception as exc:
                log.error(
                    "task.score_ecosystem.contract_error",
                    address=contract.address,
                    error=str(exc),
                )
                # Don't abort the whole ecosystem score if one contract fails
                contract_results.append({
                    "address": contract.address,
                    "role": contract.contract_role,
                    "label": contract.label,
                    "code_score": 50.0,  # neutral fallback
                    "error": str(exc),
                })

        # ── Aggregate code risk across all contracts ───────────────────────────
        aggregated_code_score = _aggregate_ecosystem_code_risk(contract_results)

        # Use primary contract for ownership + liquidity
        # (these are protocol-level properties, not per-contract)
        if primary_result is None and contract_results:
            primary_result = contract_results[0]

        ownership_score = primary_result["ownership"]["score"] if primary_result else 50.0
        liquidity_score = primary_result["liquidity"]["score"] if primary_result else 75.0

        ecosystem_result = {
            "protocol_id": protocol_id,
            "protocol_name": protocol.name,
            "scan_type": scan_type,
            "contracts_scored": len(contract_results),
            "aggregated_code_score": round(aggregated_code_score, 2),
            "ownership_score": ownership_score,
            "liquidity_score": liquidity_score,
            "contract_details": contract_results,
        }

        log.info(
            "task.score_ecosystem.complete",
            protocol_id=protocol_id,
            contracts=len(contract_results),
            code_score=aggregated_code_score,
            ownership_score=ownership_score,
            liquidity_score=liquidity_score,
        )

        return ecosystem_result

    except Exception as exc:
        log.error("task.score_ecosystem.error", protocol_id=protocol_id, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(name="app.workers.tasks.rescore_all_curated", bind=True)
def rescore_all_curated(self):
    """
    Fetch all curated protocol IDs from DB and dispatch
    one score_ecosystem subtask per protocol.
    Runs every 6 hours via Celery beat.
    """
    log.info("task.rescore_all_curated.start")

    try:
        from app.db.session import get_sync_session
        from app.db.models import Protocol

        with get_sync_session() as db:
            protocols = db.query(Protocol).all()
            protocol_ids = [str(p.id) for p in protocols]

        log.info("task.rescore_all_curated.dispatching", count=len(protocol_ids))

        # Dispatch subtasks as a Celery group (parallel)
        job = group(
            score_ecosystem.s(pid, scan_type="curated")
            for pid in protocol_ids
        )
        job.apply_async()

        return {"status": "dispatched", "protocol_count": len(protocol_ids)}

    except Exception as exc:
        log.error("task.rescore_all_curated.error", error=str(exc))
        raise


@celery_app.task(name="app.workers.tasks.rescore_watchlist_addresses", bind=True)
def rescore_watchlist_addresses(self):
    """
    Rescore all addresses on user watchlists.
    Runs daily at 2am UTC via Celery beat.
    Implemented fully on Day 10 when watchlist DB logic is added.
    """
    log.info("task.rescore_watchlist.start")
    # TODO Day 10: query watchlists table, dispatch score_contract per address
    return {"status": "stub — implemented Day 10"}


@celery_app.task(name="app.workers.tasks.refresh_ofac_list", bind=True)
def refresh_ofac_list(self):
    """
    Download OFAC SDN XML and sync to ofac_addresses table.
    Runs daily at 3am UTC. Implemented on Day 8-9.
    """
    log.info("task.refresh_ofac.start")
    # TODO Day 8-9
    return {"status": "stub — implemented Day 8-9"}


@celery_app.task(name="app.workers.tasks.check_ofac_delisting", bind=True)
def check_ofac_delisting(self):
    """
    Compare current OFAC list against previously flagged addresses.
    Auto-resolves overrides for delisted addresses.
    Runs daily at 3:30am UTC (30 min after refresh_ofac_list).
    """
    log.info("task.check_ofac_delisting.start")
    # TODO Day 8-9
    return {"status": "stub — implemented Day 8-9"}


@celery_app.task(name="app.workers.tasks.refresh_exploit_db", bind=True)
def refresh_exploit_db(self):
    """
    Pull DeFiHackLabs exploit DB and sync to exploit_records table.
    Runs weekly Sunday 4am UTC. Implemented on Day 8-9.
    """
    log.info("task.refresh_exploit_db.start")
    # TODO Day 8-9
    return {"status": "stub — implemented Day 8-9"}
