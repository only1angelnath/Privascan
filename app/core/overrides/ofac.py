"""
OFAC Multi-List Downloader, Parser, DB Sync, and Address Checker.

Official OFAC Sanctions List Service (SLS) API — File Download endpoint:
  GET https://sanctionslistservice.ofac.treas.gov/api/download/{filename}

This is the authoritative documented endpoint (per OFAC API documentation).
The old PublicationPreview/exports path and www.treasury.gov/ofac/downloads
paths are deprecated and may return errors.

Coverage:
  SDN.XML          - Specially Designated Nationals (ETH crypto addresses here)
  CONSOLIDATED.XML - All non-SDN lists combined:
                     CAPTA, FSE, CMIC, MBS, PLC, SSI, NS-ISA
  Together these two files cover every OFAC sanctions list.

XML format (flat SDN/CONSOLIDATED XML):
  <sdnEntry>
    <idList>
      <id>
        <idType>Digital Currency Address - ETH</idType>
        <idNumber>0x...</idNumber>
      </id>
    </idList>
  </sdnEntry>
"""
from __future__ import annotations
import logging
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

log = logging.getLogger(__name__)
REQUEST_TIMEOUT = 60

# ── Official OFAC SLS File Download base URL (per OFAC API documentation) ──────
SLS_DOWNLOAD_BASE = "https://sanctionslistservice.ofac.treas.gov/api/download"

HEADERS = {
    "User-Agent": "Mozilla/5.0 PrivaScan/1.0 compliance-tool",
    "Accept": "*/*",
}

# Both lists to pull — SDN + Consolidated covers all OFAC sanctions
OFAC_LISTS = [
    {
        "key": "SDN",
        "url": f"{SLS_DOWNLOAD_BASE}/SDN.XML",
        "desc": "Specially Designated Nationals",
    },
    {
        "key": "CONS",
        "url": f"{SLS_DOWNLOAD_BASE}/CONSOLIDATED.XML",
        "desc": "Consolidated (all non-SDN lists)",
    },
]


def _parse_eth_addresses(xml_text: str, source_list: str) -> list[dict]:
    """
    Parse OFAC flat XML (SDN.XML / CONSOLIDATED.XML) for ETH addresses.

    Supports two XML structures:

    1. Standard flat format (SDN.XML / CONSOLIDATED.XML):
       <sdnEntry>
         <lastName>TORNADO CASH</lastName>
         <programList><program>CYBER2</program></programList>
         <idList>
           <id>
             <idType>Digital Currency Address - ETH</idType>
             <idNumber>0x...</idNumber>
           </id>
         </idList>
       </sdnEntry>

    2. Enhanced format (SDN_ENHANCED.XML / CONS_ENHANCED.XML) — fallback:
       <feature>
         <type featureTypeId="...">Digital Currency Address - ETH</type>
         <versionDetail>0x...</versionDetail>
       </feature>
    """
    results = []
    if not xml_text or not xml_text.strip():
        log.warning("ofac.parse_empty source_list=%s", source_list)
        return results

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        log.error("ofac.parse_error list=%s: %s", source_list, exc)
        return results

    # Detect namespace if present (e.g. xmlns="https://...")
    ns_prefix = ""
    if root.tag.startswith("{"):
        ns_prefix = root.tag.split("}")[0] + "}"

    # ── Strategy 1: flat sdnEntry / idList format ─────────────────────────────
    sdn_entries = root.findall(f".//{ns_prefix}sdnEntry")

    if sdn_entries:
        for entry in sdn_entries:
            # Extract entity name
            name_el = entry.find(f"{ns_prefix}lastName")
            name = name_el.text.strip() if (name_el is not None and name_el.text) else ""

            # Extract sanctions program
            program = ""
            prog_list = entry.find(f"{ns_prefix}programList")
            if prog_list is not None:
                prog_el = prog_list.find(f"{ns_prefix}program")
                if prog_el is not None and prog_el.text:
                    program = prog_el.text.strip()

            # Extract ETH addresses from idList
            id_list = entry.find(f"{ns_prefix}idList")
            if id_list is None:
                continue

            for id_el in id_list.findall(f"{ns_prefix}id"):
                type_el = id_el.find(f"{ns_prefix}idType")
                num_el  = id_el.find(f"{ns_prefix}idNumber")
                if type_el is None or num_el is None:
                    continue
                if (type_el.text or "").strip() == "Digital Currency Address - ETH":
                    addr = (num_el.text or "").strip().lower()
                    if addr.startswith("0x") and len(addr) == 42:
                        results.append({
                            "address":     addr,
                            "name":        name,
                            "program":     program,
                            "source_list": source_list,
                        })

        log.info("ofac.parse.sdnentry list=%s eth_addresses=%d", source_list, len(results))
        return results

    # ── Strategy 2: enhanced feature format (SDN_ENHANCED / CONS_ENHANCED) ───
    # Fall back if sdnEntry is not present (different XML schema)
    for feature in root.iter():
        tag = feature.tag.split("}")[-1] if "}" in feature.tag else feature.tag
        if tag != "feature":
            continue

        ftype = feature.find(".//{*}featureType") or feature.find(".//{*}type")
        fval  = (
            feature.find(".//{*}versionDetail")
            or feature.find(".//{*}value")
        )
        if ftype is None or fval is None:
            continue

        type_text = (ftype.text or "").upper()
        if "ETH" in type_text and "DIGITAL CURRENCY" in type_text:
            addr = (fval.text or "").strip().lower()
            if addr.startswith("0x") and len(addr) == 42:
                results.append({
                    "address":     addr,
                    "name":        "",
                    "program":     "",
                    "source_list": source_list,
                })

    if results:
        log.info("ofac.parse.feature list=%s eth_addresses=%d", source_list, len(results))
    else:
        # Last resort: regex scan for any ETH address in the raw XML
        import re
        regex_addrs = re.findall(r'0x[0-9a-fA-F]{40}', xml_text)
        for addr in set(regex_addrs):
            results.append({
                "address":     addr.lower(),
                "name":        "",
                "program":     "",
                "source_list": source_list,
            })
        if results:
            log.info(
                "ofac.parse.regex_fallback list=%s eth_addresses=%d",
                source_list, len(results),
            )
        else:
            log.warning("ofac.parse.no_eth_addresses list=%s", source_list)

    return results


def _fetch_list(list_cfg: dict) -> list[dict]:
    """Download one OFAC list XML and parse ETH addresses."""
    key, url = list_cfg["key"], list_cfg["url"]
    log.info("ofac.fetch list=%s url=%s", key, url)
    try:
        resp = httpx.get(
            url,
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
            headers=HEADERS,
        )
        resp.raise_for_status()
        entries = _parse_eth_addresses(resp.text, source_list=key)
        log.info("ofac.fetch.ok list=%s eth_addresses=%d", key, len(entries))
        return entries
    except httpx.HTTPStatusError as exc:
        log.warning(
            "ofac.fetch.http_error list=%s status=%s url=%s",
            key, exc.response.status_code, url,
        )
        return []
    except Exception as exc:
        log.warning("ofac.fetch.error list=%s: %s", key, exc)
        return []


def sync_ofac_list() -> dict:
    """
    Download SDN + CONSOLIDATED XML → extract ETH addresses → upsert to ofac_addresses.

    Called by the Celery task refresh_ofac_list (daily 3am UTC).
    Also callable directly for manual syncs.

    Returns a summary dict: {added, delisted, relisted, total_active, error?}
    """
    from app.db.session import get_sync_session
    from app.db.models import OfacAddress

    log.info("ofac.sync.start fetching SDN + CONSOLIDATED from official SLS download API")

    all_entries: list[dict] = []
    for lst in OFAC_LISTS:
        all_entries.extend(_fetch_list(lst))

    if not all_entries:
        log.error("ofac.sync.failed all lists returned 0 addresses")
        return {
            "error": "All OFAC fetches failed — check network or SLS API status",
            "added": 0,
            "delisted": 0,
            "total_active": 0,
        }

    # Deduplicate — same address can appear on both SDN and CONSOLIDATED
    seen: dict[str, dict] = {}
    for entry in all_entries:
        addr = entry["address"]
        if addr not in seen:
            seen[addr] = entry
        else:
            # Merge source_list so we know which lists cover this address
            existing_source = seen[addr]["source_list"]
            new_source = entry["source_list"]
            if new_source not in existing_source:
                seen[addr]["source_list"] = f"{existing_source},{new_source}"

    fresh = set(seen.keys())
    added = delisted = relisted = 0

    with get_sync_session() as db:
        existing = {r.address: r for r in db.query(OfacAddress).all()}

        # Upsert fresh addresses
        for addr, entry in seen.items():
            if addr not in existing:
                db.add(OfacAddress(
                    address=addr,
                    name=entry["name"],
                    program=entry["program"],
                    last_updated=datetime.now(timezone.utc),
                    was_delisted=False,
                ))
                added += 1
            else:
                row = existing[addr]
                # Update metadata
                if entry["name"]:
                    row.name = entry["name"]
                if entry["program"]:
                    row.program = entry["program"]
                row.last_updated = datetime.now(timezone.utc)
                # Re-list if previously delisted
                if row.was_delisted:
                    row.was_delisted = False
                    row.delisted_at = None
                    relisted += 1

        # Mark addresses no longer in the list as delisted
        for addr, row in existing.items():
            if addr not in fresh and not row.was_delisted:
                row.was_delisted = True
                row.delisted_at = datetime.now(timezone.utc)
                delisted += 1

    log.info(
        "ofac.sync.complete added=%d delisted=%d relisted=%d total_active=%d",
        added, delisted, relisted, len(fresh),
    )
    return {
        "added":        added,
        "delisted":     delisted,
        "relisted":     relisted,
        "total_active": len(fresh),
    }


def check_ofac_delisting() -> dict:
    """Return all currently-delisted addresses."""
    from app.db.session import get_sync_session
    from app.db.models import OfacAddress
    with get_sync_session() as db:
        rows = db.query(OfacAddress).filter(OfacAddress.was_delisted == True).all()
        return {
            "delisted_count": len(rows),
            "addresses": [r.address for r in rows],
        }


async def is_ofac_sanctioned(address: str) -> bool:
    """
    Check if an address is on the active OFAC sanctions list.
    Returns True if found and NOT delisted.
    Used by the override engine for real-time score capping.
    """
    from app.db.session import AsyncSessionLocal
    from app.db.models import OfacAddress
    from sqlalchemy import select

    addr = address.lower().strip()
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(OfacAddress).where(
                    OfacAddress.address == addr,
                    OfacAddress.was_delisted == False,  # noqa: E712
                )
            )
            return result.scalar_one_or_none() is not None
    except Exception as exc:
        log.warning("ofac.check_failed address=%s: %s", addr, exc)
        return False
