from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.is_development,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Synchronous session for Celery workers ────────────────────────────────────
# Engine is created lazily on first use so the API container
# doesn't crash at import time if psycopg2 is missing.
_sync_engine = None
_SyncSessionLocal = None

def _get_sync_engine():
    global _sync_engine, _SyncSessionLocal
    if _sync_engine is None:
        from sqlalchemy import create_engine
        sync_url = settings.database_url.replace(
            "postgresql+asyncpg://", "postgresql+psycopg2://"
        )
        _sync_engine = create_engine(
            sync_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
        _SyncSessionLocal = sessionmaker(
            bind=_sync_engine,
            expire_on_commit=False,
        )
    return _sync_engine, _SyncSessionLocal

@contextmanager
def get_sync_session() -> Session:
    _, SessionLocal = _get_sync_engine()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
