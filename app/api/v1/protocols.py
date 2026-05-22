"""Protocol registry API — Day 15: list endpoint returns latest_score + contract_count."""
from __future__ import annotations
import logging
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal
from app.db.models import Protocol, ProtocolContract, ScoreReport

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def list_protocols():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Protocol).order_by(Protocol.name))
        protocols = result.scalars().all()

        counts_result = await db.execute(
            select(
                ProtocolContract.protocol_id,
                func.count(ProtocolContract.id).label("cnt"),
            ).group_by(ProtocolContract.protocol_id)
        )
        counts = {str(row[0]): row[1] for row in counts_result.fetchall()}

        latest_scores: dict[str, dict] = {}
        for p in protocols:
            sr_result = await db.execute(
                select(ScoreReport)
                .where(ScoreReport.protocol_id == p.id)
                .order_by(ScoreReport.scored_at.desc())
                .limit(1)
            )
            sr = sr_result.scalar_one_or_none()
            if sr:
                latest_scores[str(p.id)] = {
                    "grade":            sr.grade,
                    "overall_score":    float(sr.composite_score),
                    "composite_score":  float(sr.composite_score),
                    "scored_at":        sr.scored_at.isoformat() if sr.scored_at else None,
                    "override_applied": sr.override_applied,
                    "override_status":  sr.override_status,
                }

    return {
        "count": len(protocols),
        "protocols": [
            {
                "slug":           p.slug,
                "name":           p.name,
                "description":    p.description,
                "website_url":    p.website_url,
                "github_url":     p.github_url,
                "defillama_slug": p.defillama_slug,
                "contract_count": counts.get(str(p.id), 0),
                "latest_score":   latest_scores.get(str(p.id)),
            }
            for p in protocols
        ],
    }


@router.get("/{slug}/contracts")
async def get_protocol_contracts(slug: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Protocol).where(Protocol.slug == slug))
        protocol = result.scalar_one_or_none()
        if not protocol:
            raise HTTPException(status_code=404, detail=f"Protocol '{slug}' not found")
        cr = await db.execute(
            select(ProtocolContract)
            .where(ProtocolContract.protocol_id == protocol.id)
            .order_by(ProtocolContract.is_primary.desc())
        )
        contracts = cr.scalars().all()
    return {
        "slug": slug, "name": protocol.name,
        "contract_count": len(contracts),
        "contracts": [
            {"address": c.address, "chain_id": c.chain_id, "role": c.contract_role,
             "label": c.label, "is_primary": c.is_primary}
            for c in contracts
        ],
    }


@router.get("/{slug}")
async def get_protocol(slug: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Protocol).where(Protocol.slug == slug))
        protocol = result.scalar_one_or_none()
        if not protocol:
            raise HTTPException(status_code=404, detail=f"Protocol '{slug}' not found")

        cr = await db.execute(
            select(ProtocolContract)
            .where(ProtocolContract.protocol_id == protocol.id)
            .order_by(ProtocolContract.is_primary.desc())
        )
        contracts = cr.scalars().all()

        sr_result = await db.execute(
            select(ScoreReport)
            .where(ScoreReport.protocol_id == protocol.id)
            .order_by(ScoreReport.scored_at.desc())
            .limit(1)
        )
        latest_score = sr_result.scalar_one_or_none()

    score_data = None
    if latest_score:
        score_data = {
            "composite_score":  float(latest_score.composite_score),
            "overall_score":    float(latest_score.composite_score),
            "grade":            latest_score.grade,
            "override_applied": latest_score.override_applied,
            "override_status":  latest_score.override_status,
            "sub_scores": {
                "code":       float(latest_score.code_risk_score)  if latest_score.code_risk_score  else None,
                "ownership":  float(latest_score.ownership_score)  if latest_score.ownership_score  else None,
                "liquidity":  float(latest_score.liquidity_score)  if latest_score.liquidity_score  else None,
                "audit":      float(latest_score.audit_score)      if latest_score.audit_score      else None,
                "compliance": float(latest_score.compliance_score) if latest_score.compliance_score else None,
                "governance": float(latest_score.governance_score) if latest_score.governance_score else None,
            },
            "scored_at": latest_score.scored_at.isoformat() if latest_score.scored_at else None,
        }

    return {
        "slug":           protocol.slug,
        "name":           protocol.name,
        "description":    protocol.description,
        "website_url":    protocol.website_url,
        "github_url":     protocol.github_url,
        "defillama_slug": protocol.defillama_slug,
        "contract_count": len(contracts),
        "contracts": [
            {"address": c.address, "chain_id": c.chain_id, "role": c.contract_role,
             "label": c.label, "is_primary": c.is_primary}
            for c in contracts
        ],
        "latest_score": score_data,
    }
