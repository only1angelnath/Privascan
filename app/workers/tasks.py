"""
Celery tasks — Days 6-9.

IMPORTANT: Celery tasks run in separate worker processes (not the async
event loop). All tasks are sync `def`. Async code is called via asyncio.run().

Task hierarchy:
  rescore_all_curated
    └── score_ecosystem(protocol_id)   ← one per protocol
          └── score_contract(address)  ← one per contract in ecosystem
  score_contract is also called directly for community (Track B) scans.
"""

import asyncio
import os
import re
from datetime import date, datetime
from decimal import Decimal

import httpx
import structlog
from celery import group

from app.workers.celery_app import celery_app

log = structlog.get_logger()

# ── Role weights ───────────────────────────────────────────────────────────────
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
    "treasury":   0.9,
}

# ── DeFiHackLabs GitHub repo base URL ─────────────────────────────────────────
DEFIHACKLABS_README_URL = (
    "https://raw.githubusercontent.com/SunWeb3Sec/DeFiHackLabs/main/README.md"
)


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
    from app.core.clients.collector import collect_contract_data
    from app.core.scoring.code_analyser import analyse_contract
    from app.core.scoring.ownership_analyser import analyse_ownership
    from app.core.scoring.liquidity_analyser import analyse_liquidity

    raw = asyncio.run(
        collect_contract_data(
            address=address,
            chain_slug=chain_slug,
            protocol_defillama_slug=protocol_defillama_slug,
            scan_type=scan_type,
        )
    )
    code_result = asyncio.run(analyse_contract(raw))

    source_code = ""
    if raw.source and raw.source.source_code:
        source_code = raw.source.source_code

    ownership_result = None
    if raw.on_chain is not None:
        all_code_flags = [f.check for f in code_result.findings]
        if code_flags:
            all_code_flags.extend(code_flags)
        ownership_result = asyncio.run(
            analyse_ownership(
                on_chain=raw.on_chain,
                source_code=source_code,
                chain_slug=chain_slug,
                code_flags=all_code_flags,
            )
        )

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
        "ownership": (
            {
                "score": ownership_result.score,
                "flags": ownership_result.flags,
                "details": ownership_result.details,
            }
            if ownership_result
            else {"score": 50.0, "flags": [], "details": {}}
        ),
        "liquidity": {
            "score": liquidity_result.score,
            "tvl_usd": liquidity_result.tvl_usd,
            "tvl_tier": liquidity_result.tvl_tier,
            "tvl_source": liquidity_result.tvl_source,
            "tvl_confidence": liquidity_result.tvl_confidence,
        },
    }


def _aggregate_ecosystem_code_risk(contract_scores: list[dict]) -> float:
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
# SCORING TASKS
# ─────────────────────────────────────────────────────────────────────────────

@celery_app.task(
    name="app.workers.tasks.score_contract",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def score_contract(self, address: str, chain_slug: str,
                   protocol_defillama_slug: str | None = None,
                   scan_type: str = "community"):
    log.info("task.score_contract.start", address=address, chain=chain_slug)
    try:
        result = _run_single_contract_score(
            address=address,
            chain_slug=chain_slug,
            protocol_defillama_slug=protocol_defillama_slug,
            scan_type=scan_type,
        )
        log.info("task.score_contract.complete", address=address,
                 code_score=result["code"]["score"])
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
    log.info("task.score_ecosystem.start", protocol_id=protocol_id)
    try:
        from app.db.session import get_sync_session
        from app.db.models import Protocol, ProtocolContract
        from app.core.clients.chains import CHAIN_ID_TO_SLUG

        with get_sync_session() as db:
            protocol = db.query(Protocol).filter(Protocol.id == protocol_id).first()
            if not protocol:
                return {"error": f"Protocol {protocol_id} not found"}
            contracts = db.query(ProtocolContract).filter(
                ProtocolContract.protocol_id == protocol_id
            ).all()

        if not contracts:
            return {"error": "No contracts registered for this protocol"}

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
                log.error("task.score_ecosystem.contract_error",
                          address=contract.address, error=str(exc))
                contract_results.append({
                    "address": contract.address,
                    "role": contract.contract_role,
                    "label": contract.label,
                    "code_score": 50.0,
                    "error": str(exc),
                })

        aggregated_code_score = _aggregate_ecosystem_code_risk(contract_results)

        if primary_result is None and contract_results:
            primary_result = contract_results[0]

        ownership_score = primary_result["ownership"]["score"] if primary_result else 50.0
        liquidity_score = primary_result["liquidity"]["score"] if primary_result else 75.0

        from app.core.scoring.aggregator import aggregate
        from app.core.scoring.audit_analyser import analyse_audit
        from app.core.scoring.compliance_analyser import analyse_compliance

        audit_score = analyse_audit(protocol_id=protocol_id)

        # Aggregate compliance across all contracts in this protocol
        compliance_scores = [
            analyse_compliance(address=c.address)
            for c in contracts
        ]
        compliance_score = max(compliance_scores) if compliance_scores else 0.0

        governance_score = 50.0

        agg = aggregate(
            code_score=aggregated_code_score,
            ownership_score=ownership_score,
            liquidity_score=liquidity_score,
            audit_score=audit_score,
            compliance_score=compliance_score,
            governance_score=governance_score,
        )
        composite = agg["composite_score"]
        grade     = agg["grade"]

        # Save ScoreReport to DB
        import uuid
        from app.db.models import ScoreReport
        with get_sync_session() as db:
            report = ScoreReport(
                id=str(uuid.uuid4()),
                protocol_id=protocol_id,
                composite_score=round(composite, 2),
                grade=grade,
                code_risk_score=round(aggregated_code_score, 2),
                ownership_score=round(ownership_score, 2),
                liquidity_score=round(liquidity_score, 2),
                audit_score=round(audit_score, 2),
                compliance_score=round(compliance_score, 2),
                governance_score=round(governance_score, 2),
                override_applied=agg.get("override_applied", False),
                override_status=agg.get("override_status"),
                score_version="1.0",
            )
            db.add(report)
            db.commit()
            log.info("task.score_ecosystem.saved",
                     protocol=protocol.name, grade=grade, composite=composite,
                     audit=audit_score, compliance=compliance_score)

        return {
            "protocol_id":           protocol_id,
            "protocol_name":         protocol.name,
            "scan_type":             scan_type,
            "contracts_scored":      len(contract_results),
            "aggregated_code_score": round(aggregated_code_score, 2),
            "ownership_score":       ownership_score,
            "liquidity_score":       liquidity_score,
            "audit_score":           round(audit_score, 2),
            "compliance_score":      round(compliance_score, 2),
            "composite_score":       round(composite, 2),
            "grade":                 grade,
            "contract_details":      contract_results,
        }
    except Exception as exc:
        log.error("task.score_ecosystem.error", protocol_id=protocol_id, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(name="app.workers.tasks.rescore_all_curated", bind=True)
def rescore_all_curated(self):
    log.info("task.rescore_all_curated.start")
    try:
        from app.db.session import get_sync_session
        from app.db.models import Protocol
        with get_sync_session() as db:
            protocol_ids = [str(p.id) for p in db.query(Protocol).all()]
        job = group(
            score_ecosystem.s(pid, scan_type="curated") for pid in protocol_ids
        )
        job.apply_async()
        return {"status": "dispatched", "protocol_count": len(protocol_ids)}
    except Exception as exc:
        log.error("task.rescore_all_curated.error", error=str(exc))
        raise


@celery_app.task(name="app.workers.tasks.rescore_watchlist_addresses", bind=True)
def rescore_watchlist_addresses(self):
    """
    Rescore all contracts on user watchlists.
    Compares new score vs last stored score.
    If delta >= threshold → publish alert to Redis → bot sends Telegram message.
    Runs daily at 2am UTC via Celery beat.
    """
    log.info("task.rescore_watchlist.start")
    try:
        from app.db.session import get_sync_session
        from app.db.models import Watchlist, Contract, ScoreReport
        from app.core.clients.chains import CHAIN_ID_TO_SLUG
        from sqlalchemy.orm import joinedload

        with get_sync_session() as db:
            watchlists = (
                db.query(Watchlist)
                .options(joinedload(Watchlist.contract))
                .all()
            )

        if not watchlists:
            log.info("task.rescore_watchlist.no_entries")
            return {"status": "complete", "rescored": 0, "alerts_sent": 0}

        # Group by contract to avoid duplicate scoring
        seen_contracts: dict[str, dict] = {}
        for wl in watchlists:
            cid = str(wl.contract_id)
            if cid not in seen_contracts:
                seen_contracts[cid] = {"contract": wl.contract, "watchers": []}
            seen_contracts[cid]["watchers"].append({
                "chat_id":   wl.telegram_chat_id,
                "threshold": float(wl.threshold_score or 10.0),
            })

        rescored    = 0
        alerts_sent = 0

        for contract_id, data in seen_contracts.items():
            contract   = data["contract"]
            chain_slug = CHAIN_ID_TO_SLUG.get(contract.chain_id, "ethereum")

            with get_sync_session() as db:
                last_report = (
                    db.query(ScoreReport)
                    .filter(ScoreReport.contract_id == contract_id)
                    .order_by(ScoreReport.scored_at.desc())
                    .first()
                )

            old_score = float(last_report.composite_score) if last_report else None
            old_grade = last_report.grade if last_report else None

            try:
                result = _run_single_contract_score(
                    address=contract.address,
                    chain_slug=chain_slug,
                    scan_type="community",
                )
                rescored += 1
            except Exception as exc:
                log.error("task.rescore_watchlist.score_error address=%s: %s",
                          contract.address, exc)
                continue

            from app.core.scoring.audit_analyser import analyse_audit
            from app.core.scoring.compliance_analyser import analyse_compliance
            from app.core.scoring.aggregator import aggregate
            import uuid as _uuid

            with get_sync_session() as _db:
                from app.db.models import ProtocolContract as _PC
                pc_row = _db.query(_PC).filter(
                    _PC.address == contract.address,
                    _PC.chain_id == contract.chain_id,
                ).first()
                protocol_id_str = str(pc_row.protocol_id) if pc_row else None

            audit_score      = analyse_audit(protocol_id=protocol_id_str)
            compliance_score = analyse_compliance(address=contract.address)

            agg = aggregate(
                code_score=result["code"]["score"],
                ownership_score=result["ownership"]["score"],
                liquidity_score=result["liquidity"]["score"],
                audit_score=audit_score,
                compliance_score=compliance_score,
            )
            new_score = agg["composite_score"]
            new_grade = agg["grade"]

            from app.db.models import Contract as _ContractModel
            with get_sync_session() as _db2:
                c_row = _db2.query(_ContractModel).filter(
                    _ContractModel.address == contract.address,
                    _ContractModel.chain_id == contract.chain_id,
                ).first()
                if c_row:
                    _db2.add(ScoreReport(
                        id=str(_uuid.uuid4()),
                        contract_id=c_row.id,
                        protocol_id=protocol_id_str,
                        composite_score=new_score,
                        grade=new_grade,
                        code_risk_score=result["code"]["score"],
                        ownership_score=result["ownership"]["score"],
                        liquidity_score=result["liquidity"]["score"],
                        audit_score=audit_score,
                        compliance_score=compliance_score,
                        governance_score=50.0,
                        override_applied=agg["override_applied"],
                        override_status=agg["override_status"],
                    ))

            if old_score is not None:
                delta = abs(new_score - old_score)
                for watcher in data["watchers"]:
                    if delta >= watcher["threshold"]:
                        alert_payload = {
                            "chat_id":         watcher["chat_id"],
                            "address":         contract.address,
                            "chain":           chain_slug,
                            "old_score":       old_score,
                            "new_score":       new_score,
                            "old_grade":       old_grade or "?",
                            "new_grade":       new_grade,
                            "sub_scores":      agg["sub_scores"],
                            "new_flags":       result["code"].get("flags", [])[:5],
                            "override_status": agg["override_status"],
                        }
                        asyncio.run(_publish_alert_async(alert_payload))
                        alerts_sent += 1

        log.info("task.rescore_watchlist.complete rescored=%d alerts=%d",
                 rescored, alerts_sent)
        return {"status": "complete", "rescored": rescored, "alerts_sent": alerts_sent}
    except Exception as exc:
        log.error("task.rescore_watchlist.error: %s", exc)
        raise


async def _publish_alert_async(payload: dict) -> None:
    from app.bot.alerts import publish_alert
    await publish_alert(payload)


# ─────────────────────────────────────────────────────────────────────────────
# OFAC TASKS
# ─────────────────────────────────────────────────────────────────────────────

@celery_app.task(name="app.workers.tasks.refresh_ofac_list", bind=True,
                 max_retries=3, default_retry_delay=300)
def refresh_ofac_list(self):
    """
    Download OFAC SDN + CONSOLIDATED XML → extract ETH addresses → upsert.
    Delegates to app.core.overrides.ofac.sync_ofac_list() which uses the
    official OFAC SLS File Download API:
      https://sanctionslistservice.ofac.treas.gov/api/download/SDN.XML
      https://sanctionslistservice.ofac.treas.gov/api/download/CONSOLIDATED.XML

    Runs daily at 3am UTC via Celery beat.
    """
    log.info("task.refresh_ofac.start")
    try:
        from app.core.overrides.ofac import sync_ofac_list
        result = sync_ofac_list()

        if "error" in result:
            log.error("task.refresh_ofac.failed error=%s", result["error"])
            raise self.retry(exc=RuntimeError(result["error"]), countdown=300)

        log.info(
            "task.refresh_ofac.complete added=%s delisted=%s relisted=%s total_active=%s",
            result.get("added"), result.get("delisted"),
            result.get("relisted"), result.get("total_active"),
        )
        return {
            "status":       "complete",
            "added":        result.get("added", 0),
            "delisted":     result.get("delisted", 0),
            "relisted":     result.get("relisted", 0),
            "total_active": result.get("total_active", 0),
        }
    except Exception as exc:
        if not hasattr(exc, "exc"):
            log.error("task.refresh_ofac.error error=%s", str(exc))
            raise self.retry(exc=exc)
        raise


@celery_app.task(name="app.workers.tasks.check_ofac_delisting", bind=True,
                 max_retries=2, default_retry_delay=120)
def check_ofac_delisting(self):
    """
    Re-sync OFAC list and mark any addresses no longer present as delisted.
    Runs daily at 3:30am UTC (30 min after refresh_ofac_list).
    sync_ofac_list() handles delisting detection itself — addresses absent
    from the fresh download are marked was_delisted=True automatically.
    """
    log.info("task.check_ofac_delisting.start")
    try:
        from app.core.overrides.ofac import sync_ofac_list, check_ofac_delisting as _check
        sync_ofac_list()
        delisting_result = _check()
        delisted_count   = delisting_result.get("delisted_count", 0)
        log.info("task.check_ofac_delisting.complete delisted_count=%d", delisted_count)
        return {"status": "complete", "delisted_count": delisted_count}
    except Exception as exc:
        log.error("task.check_ofac_delisting.error error=%s", str(exc))
        raise self.retry(exc=exc)


# ─────────────────────────────────────────────────────────────────────────────
# DEFIHACKLABS PARSER
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_defihacklabs_via_api() -> list[dict]:
    """
    Use GitHub API to list all year-month folders in src/test,
    then fetch each .sol file and parse @KeyInfo blocks.

    Requires GITHUB_TOKEN env var on Railway worker to avoid the 60 req/hr
    unauthenticated rate limit (authenticated limit: 5,000 req/hr).
    Add to Railway worker env vars: GITHUB_TOKEN=ghp_...
    """
    records  = []
    base_url = "https://api.github.com/repos/SunWeb3Sec/DeFiHackLabs/contents/src/test"

    github_token = os.environ.get("GITHUB_TOKEN", "").strip()
    headers = {"Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"
        log.info("defihacklabs.fetch authenticated github requests")
    else:
        log.warning(
            "defihacklabs.fetch no GITHUB_TOKEN — unauthenticated limit is "
            "60 req/hr, may fail. Set GITHUB_TOKEN on Railway worker."
        )

    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            resp = client.get(base_url, headers=headers)

            if resp.status_code == 403:
                log.warning(
                    "defihacklabs.rate_limited remaining=%s — add GITHUB_TOKEN",
                    resp.headers.get("X-RateLimit-Remaining", "?"),
                )
                return []

            if resp.status_code != 200:
                log.warning("defihacklabs.api_error status=%s", resp.status_code)
                return []

            dirs = [d for d in resp.json() if d.get("type") == "dir"]
            log.info("defihacklabs.dirs_found count=%d", len(dirs))

            for d in dirs:
                year_month = d["name"]
                dir_resp   = client.get(d["url"], headers=headers)

                if dir_resp.status_code == 403:
                    log.warning("defihacklabs.rate_limited_on_dir dir=%s stopping", year_month)
                    break

                if dir_resp.status_code != 200:
                    continue

                sol_files = [f for f in dir_resp.json() if f.get("name", "").endswith(".sol")]

                for sol_file in sol_files:
                    try:
                        raw_url = sol_file.get("download_url")
                        if not raw_url:
                            continue
                        sol_resp = client.get(raw_url, timeout=15)
                        if sol_resp.status_code != 200:
                            continue
                        record = _parse_sol_file(sol_resp.text, year_month, sol_file["name"])
                        if record:
                            records.append(record)
                    except Exception as exc:
                        log.warning("defihacklabs.sol_error file=%s: %s",
                                    sol_file.get("name"), str(exc))

    except Exception as exc:
        log.warning("defihacklabs.fetch_error: %s", str(exc))

    log.info("defihacklabs.fetch.complete records=%d", len(records))
    return records


def _parse_sol_file(sol_text: str, year_month: str, filename: str) -> dict | None:
    """Parse @KeyInfo block from a DeFiHackLabs .sol exploit file."""
    protocol_name = re.sub(r"_exp.*", "", filename.replace(".sol", ""))
    protocol_name = protocol_name.replace("_", " ").strip()
    if not protocol_name:
        return None

    if not re.search(r"Total [Ll]ost", sol_text):
        return None

    try:
        parts        = year_month.split("-")
        exploit_date = datetime.strptime(f"{parts[0]}-{parts[1]}-01", "%Y-%m-%d").date()
    except Exception:
        exploit_date = None

    loss_usd = None
    keyinfo  = re.search(
        r"(?:@KeyInfo.*?Total Lost|Total lost).*?:(.+)", sol_text, re.IGNORECASE
    )
    if keyinfo:
        loss_text = keyinfo.group(1).strip()
        eth_match = re.search(r"([\d.]+)\s*ETH", loss_text, re.IGNORECASE)
        usd_match = re.search(r"\$?~?([\d,.]+)\s*([MmKkBb]?)", loss_text)
        if eth_match:
            try:
                loss_usd = Decimal(str(int(float(eth_match.group(1)) * 2500)))
            except Exception:
                pass
        elif usd_match:
            try:
                amount = float(usd_match.group(1).replace(",", ""))
                suffix = usd_match.group(2).upper()
                if suffix == "M":   amount *= 1_000_000
                elif suffix == "K": amount *= 1_000
                elif suffix == "B": amount *= 1_000_000_000
                loss_usd = Decimal(str(int(amount)))
            except Exception:
                pass

    vuln_match = re.search(
        r"(?:Vulnerable Contract|Attack Contract).*?0x([0-9a-fA-F]{40})",
        sol_text, re.IGNORECASE,
    )
    contract_address = None
    if vuln_match:
        contract_address = "0x" + vuln_match.group(1).lower()
    else:
        addrs = re.findall(r"0x[0-9a-fA-F]{40}", sol_text[:800])
        if addrs:
            contract_address = addrs[-1].lower()

    attack_type = "Unknown"
    for kw in ["Flash Loan", "Reentrancy", "Price Manipulation", "Access Control",
               "Logic Error", "Rugpull", "Oracle Manipulation", "Integer Overflow"]:
        if kw.lower() in sol_text.lower():
            attack_type = kw
            break

    return {
        "protocol_name":    protocol_name,
        "contract_address": contract_address,
        "exploit_date":     exploit_date,
        "loss_usd":         loss_usd,
        "exploit_type":     attack_type,
        "is_resolved":      False,
    }


@celery_app.task(name="app.workers.tasks.refresh_exploit_db", bind=True,
                 max_retries=3, default_retry_delay=300)
def refresh_exploit_db(self):
    """
    Pull DeFiHackLabs .sol files via GitHub API → parse → upsert exploit_records.
    Runs weekly Sunday 4am UTC.
    """
    log.info("task.refresh_exploit_db.start")
    try:
        records = _fetch_defihacklabs_via_api()
        log.info("task.refresh_exploit_db.parsed record_count=%d", len(records))

        if not records:
            log.warning("task.refresh_exploit_db.no_records")
            return {"status": "complete", "records_found": 0}

        from app.db.session import get_sync_session
        from app.db.models import ExploitRecord

        inserted = 0
        skipped  = 0

        with get_sync_session() as db:
            for rec in records:
                existing = db.query(ExploitRecord).filter(
                    ExploitRecord.protocol_name == rec["protocol_name"],
                    ExploitRecord.exploit_date  == rec["exploit_date"],
                ).first()

                if existing:
                    skipped += 1
                    continue

                db.add(ExploitRecord(
                    protocol_name=rec["protocol_name"],
                    contract_address=rec["contract_address"],
                    exploit_date=rec["exploit_date"],
                    loss_usd=rec["loss_usd"],
                    exploit_type=rec["exploit_type"],
                    is_resolved=False,
                ))
                inserted += 1

        log.info("task.refresh_exploit_db.complete inserted=%d skipped=%d",
                 inserted, skipped)
        return {
            "status":            "complete",
            "records_parsed":    len(records),
            "inserted":          inserted,
            "skipped_duplicates": skipped,
        }
    except Exception as exc:
        log.error("task.refresh_exploit_db.error error=%s", str(exc))
        raise self.retry(exc=exc)