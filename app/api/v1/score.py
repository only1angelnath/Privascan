"""
Day 7 — Real score endpoints.  (updated Day 9: audit + compliance wired)

The scoring pipeline (Slither) is CPU-bound and synchronous.
Running it inline in an async handler blocks the FastAPI event loop.
Fix: run the heavy parts in a ThreadPoolExecutor via asyncio.run_in_executor(),
with a 120s timeout. This keeps the API responsive.
"""

from __future__ import annotations

import re
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from celery.result import AsyncResult

from app.core.cache import get_cached_score, set_cached_score
from app.core.scoring.aggregator import aggregate
from app.core.clients.chains import CHAINS
from app.workers.celery_app import celery_app
from app.core.overrides.engine import apply_overrides
from app.api.v1.auth import get_api_key

log = logging.getLogger(__name__)
router = APIRouter()

ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

# One thread per score request — Slither needs its own thread
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="slither")

# Timeout for the full pipeline in seconds
PIPELINE_TIMEOUT = 120


def _validate(chain: str, address: str) -> None:
    if chain not in CHAINS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported chain '{chain}'. Supported: {', '.join(CHAINS)}",
        )
    if not ADDRESS_RE.match(address):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid EVM address '{address}'. Must be 0x + 40 hex chars.",
        )


def _run_pipeline_sync(address: str, chain_slug: str) -> dict:
    """
    Synchronous version of the full pipeline — runs in a thread.
    Uses asyncio.run() internally to call async clients.
    Slither runs synchronously inside this thread.
    """
    from app.core.clients.collector import collect_contract_data
    from app.core.scoring.code_analyser import analyse_contract
    from app.core.scoring.ownership_analyser import analyse_ownership
    from app.core.scoring.liquidity_analyser import analyse_liquidity
    from app.core.scoring.audit_analyser import analyse_audit
    from app.core.scoring.compliance_analyser import analyse_compliance

    chain = CHAINS[chain_slug]

    # Each thread gets its own event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # ── 1. Collect (async I/O) ────────────────────────────────────────────
        raw = loop.run_until_complete(
            collect_contract_data(address=address, chain_slug=chain_slug)
        )

        # ── 2. Code risk — Slither runs synchronously here ────────────────────
        code_result = loop.run_until_complete(analyse_contract(raw))

        # ── 3. Ownership (async RPC calls) ────────────────────────────────────
        source_code = ""
        if raw.source and raw.source.source_code:
            source_code = raw.source.source_code

        ownership_result = None
        if raw.on_chain:
            code_flags = [f.check for f in code_result.findings]
            ownership_result = loop.run_until_complete(
                analyse_ownership(
                    on_chain=raw.on_chain,
                    source_code=source_code,
                    chain_slug=chain_slug,
                    code_flags=code_flags,
                )
            )

        # ── 4. Liquidity (pure math — no I/O) ────────────────────────────────
        liquidity_result = analyse_liquidity(
            tvl=raw.tvl,
            address=address,
            chain_id=chain.chain_id,
        )

    finally:
        loop.close()

    # ── 5. Audit sub-score (sync DB query — community scan has no protocol_id) ─
    audit_score = analyse_audit(protocol_id=None)

    # ── 6. Compliance sub-score (sync DB query) ───────────────────────────────
    compliance_score = analyse_compliance(address=address)

    # ── 7. Aggregate ──────────────────────────────────────────────────────────
    agg = aggregate(
        code_score=code_result.score,
        ownership_score=ownership_result.score if ownership_result else 50.0,
        liquidity_score=liquidity_result.score,
        audit_score=audit_score,
        compliance_score=compliance_score,
        address=address,
    )

    tvl_source = raw.tvl.source if raw.tvl else "none"

    return {
        "address": address,
        "chain": chain_slug,
        "chain_id": chain.chain_id,
        "scan_type": "community",
        "composite_score": agg["composite_score"],
        "grade": agg["grade"],
        "grade_label": {
            "A": "Low Risk", "B": "Moderate-Low Risk",
            "C": "Moderate Risk", "D": "High Risk", "F": "Critical Risk",
        }.get(agg["grade"], "Unknown"),
        "override_applied": agg["override_applied"],
        "override_status": agg["override_status"],
        "sub_scores": agg["sub_scores"],
        "details": {
            "code": {
                "score": code_result.score,
                "is_verified": code_result.is_verified,
                "high_count": code_result.high_count,
                "medium_count": code_result.medium_count,
                "low_count": code_result.low_count,
                "findings": [
                    {
                        "check": f.check,
                        "impact": f.impact,
                        "confidence": f.confidence,
                        "description": f.description,
                        "is_custom": f.is_custom,
                    }
                    for f in code_result.findings
                ],
                "error": code_result.error,
            },
            "ownership": {
                "score": ownership_result.score if ownership_result else 50.0,
                "flags": ownership_result.flags if ownership_result else [],
                "details": ownership_result.details if ownership_result else {},
            },
            "liquidity": {
                "score": liquidity_result.score,
                "tvl_usd": liquidity_result.tvl_usd,
                "tvl_tier": liquidity_result.tvl_tier,
                "tvl_source": liquidity_result.tvl_source,
                "tvl_confidence": liquidity_result.tvl_confidence,
            },
            "audit": {
                "score": audit_score,
                "note": "Community scan — no protocol audit records linked",
            },
            "compliance": {
                "score": compliance_score,
            },
        },
        "scored_at": agg["scored_at"],
        "cached": False,
        "_tvl_source_internal": tvl_source,
    }


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/task/{task_id}")
async def poll_task(task_id: str):
    """Poll the status of an async scan task dispatched via POST /request."""
    task = AsyncResult(task_id, app=celery_app)
    if task.state == "PENDING":
        return {"task_id": task_id, "status": "pending"}
    elif task.state == "SUCCESS":
        return {"task_id": task_id, "status": "complete", "result": task.result}
    elif task.state == "FAILURE":
        return {"task_id": task_id, "status": "failed", "error": str(task.info)}
    else:
        return {"task_id": task_id, "status": task.state.lower()}


@router.post("/request")
async def request_scan(
    body: dict,
    request: Request,
    api_key_info: dict = Depends(get_api_key),
):
    """
    Trigger an async community scan via Celery worker.
    Returns immediately with task_id — poll GET /task/{task_id} for result.
    """
    address = body.get("address", "")
    chain = body.get("chain", "ethereum")
    _validate(chain, address)

    from app.workers.tasks import score_contract
    task = score_contract.apply_async(
        kwargs={"address": address, "chain_slug": chain, "scan_type": "community"}
    )
    return {
        "task_id": task.id,
        "status": "queued",
        "address": address,
        "chain": chain,
        "poll_url": f"/api/v1/score/task/{task.id}",
    }


@router.get("/{chain}/{address}/history")
async def get_score_history(
    chain: str,
    address: str,
    limit: int = Query(default=30, ge=1, le=100),
):
    """Last N score reports from the score_reports table."""
    _validate(chain, address)

    from app.db.session import AsyncSessionLocal
    from app.db.models import Contract, ScoreReport
    from sqlalchemy import select

    addr = address.lower()

    async with AsyncSessionLocal() as db:
        # Find the contract row
        contract_result = await db.execute(
            select(Contract).where(
                Contract.address == addr,
                Contract.chain_name == chain,
            )
        )
        contract = contract_result.scalar_one_or_none()

        if not contract:
            return {"address": address, "chain": chain, "history": []}

        # Fetch score reports ordered newest first
        reports_result = await db.execute(
            select(ScoreReport)
            .where(ScoreReport.contract_id == contract.id)
            .order_by(ScoreReport.scored_at.desc())
            .limit(limit)
        )
        reports = reports_result.scalars().all()

    history = [
        {
            "composite_score": float(r.composite_score),
            "grade": r.grade,
            "code_risk_score": float(r.code_risk_score) if r.code_risk_score else None,
            "ownership_score": float(r.ownership_score) if r.ownership_score else None,
            "liquidity_score": float(r.liquidity_score) if r.liquidity_score else None,
            "audit_score": float(r.audit_score) if r.audit_score else None,
            "compliance_score": float(r.compliance_score) if r.compliance_score else None,
            "override_applied": r.override_applied,
            "override_status": r.override_status,
            "scored_at": r.scored_at.isoformat() if r.scored_at else None,
        }
        for r in reports
    ]

    return {"address": address, "chain": chain, "history": history}


@router.get("/{chain}/{address}")
async def get_score(
    chain: str,
    address: str,
    request: Request,
    api_key_info: dict = Depends(get_api_key),
):
    """
    Score any EVM contract. Returns cached result if fresh.

    First call: runs full pipeline in thread (~30-60s for Slither).
    Second call: returns from Redis cache instantly.
    """
    _validate(chain, address)

    # ── Cache check — return instantly if fresh ───────────────────────────────
    cached = await get_cached_score(chain, address)
    if cached:
        cached["cached"] = True
        return cached

    # ── Run pipeline in thread — keeps event loop free ────────────────────────
    log.info("score.pipeline.start chain=%s address=%s", chain, address)
    loop = asyncio.get_event_loop()

    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(_executor, _run_pipeline_sync, address, chain),
            timeout=PIPELINE_TIMEOUT,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"Scoring timed out after {PIPELINE_TIMEOUT}s. "
                   f"Use POST /api/v1/score/request for async scanning.",
        )
    except Exception as exc:
        log.error("score.pipeline.error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Scoring pipeline failed: {str(exc)[:300]}",
        )

    # Strip internal key before returning
    tvl_source = result.pop("_tvl_source_internal", "none")

    # Apply OFAC + exploit overrides (hard caps on total score)
    result = await apply_overrides(address, result)

    # Cache the result
    await set_cached_score(
        chain_slug=chain,
        address=address,
        data=result,
        tvl_source=tvl_source,
        scan_type="community",
    )

    log.info(
        "score.pipeline.complete chain=%s address=%s score=%.1f grade=%s",
        chain, address, result["composite_score"], result["grade"],
    )
    return result
