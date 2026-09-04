from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

_engine=None; _sessions=None

def _session_factory():
    global _engine,_sessions
    if not settings.database_url: raise RuntimeError("DATABASE_URL is required for database operations")
    if _sessions is None:
        _engine=create_async_engine(settings.database_url,pool_pre_ping=True,pool_size=settings.db_pool_size,max_overflow=settings.db_max_overflow)
        _sessions=async_sessionmaker(_engine,class_=AsyncSession,expire_on_commit=False)
    return _sessions

async def tenant_session(organization_id:str)->AsyncGenerator[AsyncSession,None]:
    if not organization_id: raise ValueError("organization_id is required")
    async with _session_factory()() as session:
        try:
            await session.execute(text("select set_config('app.clerk_org_id', :org_id, true)"),{"org_id":organization_id})
            yield session
            await session.commit()
        except Exception:
            await session.rollback(); raise

async def close_database() -> None:
    global _engine,_sessions
    if _engine is not None:
        await _engine.dispose()
    _engine=None; _sessions=None
