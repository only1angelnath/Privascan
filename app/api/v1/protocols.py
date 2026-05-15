"""
Day 9 — Protocol registry API (real DB queries, stubs removed).
"""
from __future__ import annotations
import logging
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models import Protocol, ProtocolContract, ScoreReport

log = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def list_protocols():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Protocol).order_by(Protocol.name))
        protocols = result.scalars().all()
    return {
        "count": len(protocols),
        "protocols": [
            {
                "slug": p.slug,
                "name": p.name,
                "description": p.description,
                "website_url": p.website_url,
                "github_url": p.github_url,
                "defillama_slug": p.defillama_slug,
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
        contracts_result = await db.execute(
            select(ProtocolContract)
            .where(ProtocolContract.protocol_id == protocol.id)
            .order_by(ProtocolContract.is_primary.desc())
        )
        contracts = contracts_result.scalars().all()
    return {
        "slug": slug,
        "name": protocol.name,
        "contract_count": len(contracts),
        "contracts": [
            {
                "address": c.address,
                "chain_id": c.chain_id,
                "role": c.contract_role,
                "label": c.label,
                "is_primary": c.is_primary,
            }
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
        contracts_result = await db.execute(
            select(ProtocolContract)
            .where(ProtocolContract.protocol_id == protocol.id)
            .order_by(ProtocolContract.is_primary.desc())
        )
        contracts = contracts_result.scalars().all()
        score_result = await db.execute(
            select(ScoreReport)
            .where(ScoreReport.protocol_id == protocol.id)
            .order_by(ScoreReport.scored_at.desc())
            .limit(1)
        )
        latest_score = score_result.scalar_one_or_none()

    score_data = None
    if latest_score:
        score_data = {
            "composite_score": float(latest_score.composite_score),
            "grade": latest_score.grade,
            "override_applied": latest_score.override_applied,
            "scored_at": latest_score.scored_at.isoformat() if latest_score.scored_at else None,
        }

    return {
        "slug": protocol.slug,
        "name": protocol.name,
        "description": protocol.description,
        "website_url": protocol.website_url,
        "github_url": protocol.github_url,
        "defillama_slug": protocol.defillama_slug,
        "contracts": [
            {
                "address": c.address,
                "chain_id": c.chain_id,
                "role": c.contract_role,
                "label": c.label,
                "is_primary": c.is_primary,
            }
            for c in contracts
        ],
        "latest_score": score_data,
    }
