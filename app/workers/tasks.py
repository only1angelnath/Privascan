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
import csv
import io
import re
import xml.etree.ElementTree as ET
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

# ── OFAC SDN XML URL ───────────────────────────────────────────────────────────
OFAC_SDN_URL = "https://www.treasury.gov/ofac/downloads/consolidated/consolidated.xml"

# ── DeFiHackLabs CSV URL ───────────────────────────────────────────────────────
DEFIHACKLABS_CSV_URL = (
    "https://raw.githubusercontent.com/SunWeb3Sec/DeFiHackLabs/"
    "main/src/test/Exploit.t.sol"
)
# We parse the README which has the structured table
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

        return {
            "protocol_id": protocol_id,
            "protocol_name": protocol.name,
            "scan_type": scan_type,
            "contracts_scored": len(contract_results),
            "aggregated_code_score": round(aggregated_code_score, 2),
            "ownership_score": ownership_score,
            "liquidity_score": liquidity_score,
            "contract_details": contract_results,
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
    log.info("task.rescore_watchlist.start")
    # Implemented Day 10
    return {"status": "stub — implemented Day 10"}


# ─────────────────────────────────────────────────────────────────────────────
# OFAC TASKS
# ─────────────────────────────────────────────────────────────────────────────

def _extract_eth_addresses_from_sdn(xml_text: str) -> set[str]:
    """
    Parse OFAC SDN XML and extract all Ethereum addresses.
    Addresses appear in <feature> blocks with type 'Digital Currency Address - ETH'.
    """
    addresses = set()
    try:
        root = ET.fromstring(xml_text)
        ns = {"ofac": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML"}

        # Try namespaced parse first
        for feature in root.iter():
            tag = feature.tag.split("}")[-1] if "}" in feature.tag else feature.tag
            if tag == "feature":
                ftype = feature.find(".//{*}featureType")
                fval  = feature.find(".//{*}versionDetail")
                if ftype is not None and fval is not None:
                    if "ETH" in (ftype.text or "").upper():
                        addr = (fval.text or "").strip().lower()
                        if re.match(r"^0x[0-9a-f]{40}$", addr):
                            addresses.add(addr)
    except ET.ParseError as e:
        log.warning("ofac.xml_parse_error", error=str(e))

    # Fallback: regex scan for any 0x ETH addresses in the raw XML
    fallback = re.findall(r'0x[0-9a-fA-F]{40}', xml_text)
    for addr in fallback:
        addresses.add(addr.lower())

    return addresses


@celery_app.task(name="app.workers.tasks.refresh_ofac_list", bind=True,
                 max_retries=3, default_retry_delay=300)
def refresh_ofac_list(self):
    """
    Download OFAC SDN XML → extract ETH addresses → upsert to ofac_addresses.
    Runs daily at 3am UTC.
    """
    log.info("task.refresh_ofac.start")
    try:
        # Download SDN list
        with httpx.Client(timeout=60.0, follow_redirects=True) as client:
            resp = client.get(OFAC_SDN_URL)
            resp.raise_for_status()
        xml_text = resp.text
        addresses = _extract_eth_addresses_from_sdn(xml_text)
        log.info("task.refresh_ofac.parsed", address_count=len(addresses))

        if not addresses:
            log.warning("task.refresh_ofac.no_addresses_found")
            return {"status": "complete", "addresses_found": 0}

        # Upsert to DB
        from app.db.session import get_sync_session
        from app.db.models import OfacAddress

        inserted = 0
        already_exists = 0

        with get_sync_session() as db:
            existing = {
                r.address for r in db.query(OfacAddress.address).all()
            }
            for addr in addresses:
                if addr in existing:
                    already_exists += 1
                    continue
                db.add(OfacAddress(
                    address=addr,
                    listed_at=datetime.utcnow(),
                    was_delisted=False,
                ))
                inserted += 1

        log.info("task.refresh_ofac.complete",
                 inserted=inserted, already_exists=already_exists)
        return {
            "status": "complete",
            "addresses_found": len(addresses),
            "inserted": inserted,
            "already_exists": already_exists,
        }
    except httpx.HTTPError as exc:
        log.error("task.refresh_ofac.http_error", error=str(exc))
        raise self.retry(exc=exc)
    except Exception as exc:
        log.error("task.refresh_ofac.error", error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(name="app.workers.tasks.check_ofac_delisting", bind=True,
                 max_retries=2, default_retry_delay=120)
def check_ofac_delisting(self):
    """
    Compare current OFAC SDN list against previously flagged addresses.
    Any address no longer present → mark was_delisted=True, set delisted_at.
    Runs daily at 3:30am UTC (30 min after refresh_ofac_list).
    """
    log.info("task.check_ofac_delisting.start")
    try:
        # Re-download current SDN (refresh_ofac_list already ran 30min ago,
        # but we need the current set to compare)
        with httpx.Client(timeout=60.0, follow_redirects=True) as client:
            resp = client.get(OFAC_SDN_URL)
            resp.raise_for_status()
        current_addresses = _extract_eth_addresses_from_sdn(resp.text)

        from app.db.session import get_sync_session
        from app.db.models import OfacAddress

        delisted = 0
        with get_sync_session() as db:
            # Get all addresses still marked as active (not yet delisted)
            active_rows = db.query(OfacAddress).filter(
                OfacAddress.was_delisted == False  # noqa: E712
            ).all()

            for row in active_rows:
                if row.address not in current_addresses:
                    row.was_delisted = True
                    row.delisted_at = datetime.utcnow()
                    delisted += 1
                    log.info("task.check_ofac_delisting.resolved",
                             address=row.address)

        log.info("task.check_ofac_delisting.complete", delisted=delisted)
        return {"status": "complete", "delisted_count": delisted}
    except Exception as exc:
        log.error("task.check_ofac_delisting.error", error=str(exc))
        raise self.retry(exc=exc)


# ─────────────────────────────────────────────────────────────────────────────
# DEFIHACKLABS PARSER
# ─────────────────────────────────────────────────────────────────────────────

def _parse_defihacklabs_readme(markdown_text: str) -> list[dict]:
    """
    Parse the DeFiHackLabs README.md exploit table.

    Table format (markdown):
    | Date | Project | Funds Lost | Type | ... |

    We extract rows where we can identify an EVM address, date, and loss amount.
    Addresses appear in the 'Link' column or inline in rows.
    """
    records = []
    lines = markdown_text.splitlines()

    in_table = False
    headers = []

    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            in_table = False
            continue

        cells = [c.strip() for c in line.strip("|").split("|")]

        # Detect header row
        if not in_table and any(
            h in ("".join(cells)).lower()
            for h in ["date", "project", "funds", "lost"]
        ):
            headers = [c.lower().replace(" ", "_") for c in cells]
            in_table = True
            continue

        # Skip separator rows
        if all(set(c.replace("-", "").replace(":", "").replace(" ", "")) <= {""} for c in cells):
            continue

        if not in_table or not headers:
            continue

        row = dict(zip(headers, cells))

        # Extract date
        raw_date = row.get("date", "") or row.get("time", "")
        parsed_date = None
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                parsed_date = datetime.strptime(raw_date[:10], fmt).date()
                break
            except ValueError:
                continue

        # Extract loss amount (look for $ figures)
        loss_text = row.get("funds_lost", "") or row.get("amount", "") or ""
        loss_usd = None
        loss_match = re.search(r"\$?([\d,]+(?:\.\d+)?)\s*([MmKkBb]?)", loss_text.replace(",", ""))
        if loss_match:
            try:
                amount = float(loss_match.group(1))
                suffix = loss_match.group(2).upper()
                if suffix == "M":
                    amount *= 1_000_000
                elif suffix == "K":
                    amount *= 1_000
                elif suffix == "B":
                    amount *= 1_000_000_000
                loss_usd = Decimal(str(int(amount)))
            except (ValueError, Exception):
                pass

        # Extract contract address from any cell
        all_text = " ".join(cells)
        addr_matches = re.findall(r'0x[0-9a-fA-F]{40}', all_text)
        contract_address = addr_matches[0].lower() if addr_matches else None

        # Extract protocol name
        protocol_name = (
            row.get("project", "") or
            row.get("protocol", "") or
            row.get("name", "")
        ).strip()
        # Strip markdown links: [Name](url) → Name
        protocol_name = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', protocol_name)

        if not protocol_name:
            continue

        records.append({
            "protocol_name": protocol_name,
            "contract_address": contract_address,
            "exploit_date": parsed_date,
            "loss_usd": loss_usd,
            "exploit_type": row.get("type", "") or row.get("attack_type", ""),
            "is_resolved": False,  # default — manual resolution via admin endpoint
        })

    return records


@celery_app.task(name="app.workers.tasks.refresh_exploit_db", bind=True,
                 max_retries=3, default_retry_delay=300)
def refresh_exploit_db(self):
    """
    Pull DeFiHackLabs README → parse exploit table → upsert to exploit_records.
    Runs weekly Sunday 4am UTC.
    """
    log.info("task.refresh_exploit_db.start")
    try:
        with httpx.Client(timeout=60.0, follow_redirects=True) as client:
            resp = client.get(DEFIHACKLABS_README_URL)
            resp.raise_for_status()

        records = _parse_defihacklabs_readme(resp.text)
        log.info("task.refresh_exploit_db.parsed", record_count=len(records))

        if not records:
            log.warning("task.refresh_exploit_db.no_records")
            return {"status": "complete", "records_found": 0}

        from app.db.session import get_sync_session
        from app.db.models import ExploitRecord

        inserted = 0
        skipped = 0

        with get_sync_session() as db:
            for rec in records:
                # Deduplicate: skip if same protocol + date already exists
                existing = db.query(ExploitRecord).filter(
                    ExploitRecord.protocol_name == rec["protocol_name"],
                    ExploitRecord.exploit_date == rec["exploit_date"],
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

        log.info("task.refresh_exploit_db.complete",
                 inserted=inserted, skipped=skipped)
        return {
            "status": "complete",
            "records_parsed": len(records),
            "inserted": inserted,
            "skipped_duplicates": skipped,
        }
    except httpx.HTTPError as exc:
        log.error("task.refresh_exploit_db.http_error", error=str(exc))
        raise self.retry(exc=exc)
    except Exception as exc:
        log.error("task.refresh_exploit_db.error", error=str(exc))
        raise self.retry(exc=exc)
