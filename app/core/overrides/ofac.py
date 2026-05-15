"""
OFAC Multi-List Downloader, Parser, DB Sync, and Address Checker.

OFAC moved to a new Sanctions List Service (SLS) host in May 2024.
New base: https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/
Requests require a User-Agent header or they get 403.

Coverage:
  SDN.XML          - Specially Designated Nationals (crypto addresses most common here)
  CONSOLIDATED.XML - All non-SDN lists combined:
                     CAPTA, FSE, CMIC, MBS, PLC, SSI, NS-ISA
  Together these two files cover every OFAC sanctions list.
"""
from __future__ import annotations
import logging
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

log = logging.getLogger(__name__)
REQUEST_TIMEOUT = 60

SLS_BASE = "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports"
HEADERS  = {"User-Agent": "Mozilla/5.0 PrivaScan/1.0 compliance-tool"}

OFAC_LISTS = [
    {"key": "SDN",  "url": f"{SLS_BASE}/SDN.XML",          "desc": "Specially Designated Nationals"},
    {"key": "CONS", "url": f"{SLS_BASE}/CONSOLIDATED.XML",  "desc": "Consolidated (all non-SDN lists)"},
]


def _parse_eth_addresses(xml_text: str, source_list: str) -> list[dict]:
    results = []
    try:
        root = ET.fromstring(xml_text)
        ns = root.tag.split("}")[0] + "}" if root.tag.startswith("{") else ""
        for entry in root.findall(f"{ns}sdnEntry"):
            name_el = entry.find(f"{ns}lastName")
            name = name_el.text.strip() if name_el is not None and name_el.text else ""
            program = ""
            prog_list = entry.find(f"{ns}programList")
            if prog_list is not None:
                prog_el = prog_list.find(f"{ns}program")
                if prog_el is not None and prog_el.text:
                    program = prog_el.text.strip()
            id_list = entry.find(f"{ns}idList")
            if id_list is None:
                continue
            for id_el in id_list.findall(f"{ns}id"):
                type_el = id_el.find(f"{ns}idType")
                num_el  = id_el.find(f"{ns}idNumber")
                if type_el is None or num_el is None:
                    continue
                if (type_el.text or "").strip() == "Digital Currency Address - ETH":
                    addr = (num_el.text or "").strip().lower()
                    if addr.startswith("0x") and len(addr) == 42:
                        results.append({"address": addr, "name": name,
                                        "program": program, "source_list": source_list})
    except ET.ParseError as exc:
        log.error("ofac.parse_error list=%s: %s", source_list, exc)
    return results


def _fetch_list(list_cfg: dict) -> list[dict]:
    key, url = list_cfg["key"], list_cfg["url"]
    log.info("ofac.fetch list=%s", key)
    try:
        resp = httpx.get(url, timeout=REQUEST_TIMEOUT,
                         follow_redirects=True, headers=HEADERS)
        resp.raise_for_status()
        entries = _parse_eth_addresses(resp.text, source_list=key)
        log.info("ofac.fetch.ok list=%s eth_addresses=%d", key, len(entries))
        return entries
    except Exception as exc:
        log.warning("ofac.fetch.error list=%s: %s", key, exc)
        return []


def sync_ofac_list() -> dict:
    from app.db.session import get_sync_session
    from app.db.models import OfacAddress
    log.info("ofac.sync.start fetching SDN + CONSOLIDATED")
    all_entries: list[dict] = []
    for lst in OFAC_LISTS:
        all_entries.extend(_fetch_list(lst))
    if not all_entries:
        return {"error": "all OFAC fetches failed", "added": 0, "delisted": 0, "total_active": 0}
    seen: dict[str, dict] = {}
    for entry in all_entries:
        addr = entry["address"]
        if addr not in seen:
            seen[addr] = entry
        elif entry["source_list"] not in seen[addr]["source_list"]:
            seen[addr]["source_list"] += f",{entry['source_list']}"
    fresh = set(seen.keys())
    added = delisted = relisted = 0
    with get_sync_session() as db:
        existing = {r.address: r for r in db.query(OfacAddress).all()}
        for addr, entry in seen.items():
            if addr not in existing:
                db.add(OfacAddress(address=addr, name=entry["name"], program=entry["program"],
                                   last_updated=datetime.now(timezone.utc), was_delisted=False))
                added += 1
            else:
                row = existing[addr]
                row.name = entry["name"]
                row.program = entry["program"]
                row.last_updated = datetime.now(timezone.utc)
                if row.was_delisted:
                    row.was_delisted = False
                    row.delisted_at = None
                    relisted += 1
        for addr, row in existing.items():
            if addr not in fresh and not row.was_delisted:
                row.was_delisted = True
                row.delisted_at = datetime.now(timezone.utc)
                delisted += 1
    log.info("ofac.sync.complete added=%d delisted=%d relisted=%d total=%d",
             added, delisted, relisted, len(fresh))
    return {"added": added, "delisted": delisted, "relisted": relisted, "total_active": len(fresh)}


def check_ofac_delisting() -> dict:
    from app.db.session import get_sync_session
    from app.db.models import OfacAddress
    with get_sync_session() as db:
        rows = db.query(OfacAddress).filter(OfacAddress.was_delisted == True).all()
        return {"delisted_count": len(rows), "addresses": [r.address for r in rows]}


async def is_ofac_sanctioned(address: str) -> bool:
    from app.db.session import AsyncSessionLocal
    from app.db.models import OfacAddress
    from sqlalchemy import select
    addr = address.lower().strip()
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OfacAddress).where(
                    OfacAddress.address == addr,
                    OfacAddress.was_delisted == False
                )
            )
            return result.scalar_one_or_none() is not None
    except Exception as exc:
        log.warning("ofac.check_failed address=%s: %s", addr, exc)
        return False
