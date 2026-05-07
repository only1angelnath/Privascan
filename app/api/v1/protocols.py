from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_protocols():
    return {"status": "stub", "protocols": []}

@router.get("/{slug}")
async def get_protocol(slug: str):
    return {"status": "stub", "slug": slug}

@router.get("/{slug}/contracts")
async def get_protocol_contracts(slug: str):
    return {"status": "stub", "slug": slug, "contracts": []}
