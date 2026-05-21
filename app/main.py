import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import api_router
from app.api.admin import router as admin_router

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("privascan.startup", env=settings.app_env)
    # Trigger curated protocol rescores on startup (non-blocking)
    try:
        from app.workers.tasks import score_ecosystem
        from app.db.database import AsyncSessionLocal
        from app.db import models
        from sqlalchemy import select
        import asyncio

        async def _trigger_startup_scans():
            await asyncio.sleep(10)  # wait for DB to be ready
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(models.Protocol))
                protocols = result.scalars().all()
                for protocol in protocols:
                    score_ecosystem.delay(str(protocol.id))
                log.info("privascan.startup_scans_queued", count=len(protocols))

        asyncio.create_task(_trigger_startup_scans())
    except Exception as exc:
        log.warning("privascan.startup_scans_failed", error=str(exc))
    yield
    log.info("privascan.shutdown")


app = FastAPI(
    title="PrivaScan API",
    description="EVM privacy protocol smart contract risk scoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/admin", tags=["admin"])
