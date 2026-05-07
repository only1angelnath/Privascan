from fastapi import APIRouter, Path

router = APIRouter()

@router.get("/{chain}/{address}")
async def get_score(chain: str, address: str):
    return {"status": "stub", "chain": chain, "address": address}

@router.get("/{chain}/{address}/history")
async def get_score_history(chain: str, address: str):
    return {"status": "stub", "chain": chain, "address": address, "history": []}

@router.get("/task/{task_id}")
async def poll_task(task_id: str):
    return {"status": "stub", "task_id": task_id}

@router.post("/request")
async def request_scan(body: dict):
    return {"status": "stub", "message": "Scan request queued"}
