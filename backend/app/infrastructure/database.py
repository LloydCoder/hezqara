from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

_engine=None; _sessions=None

def _session_factory():
    global _engine,_sessions
    if not settings.database_url: raise RuntimeError('DATABASE_URL is required for database operations')
    if _sessions is None:
        _engine=create_async_engine(settings.database_url,pool_pre_ping=True,pool_size=settings.db_pool_size,max_overflow=settings.db_max_overflow)
        _sessions=async_sessionmaker(_engine,class_=AsyncSession,expire_on_commit=False)
    return _sessions

@asynccontextmanager
async def tenant_session_context(organization_id:str):
    if not organization_id: raise ValueError('organization_id is required')
    async with _session_factory()() as session:
        try:
            await session.execute(text("select set_config('app.clerk_org_id', :org_id, true)"),{'org_id':organization_id})
            # The database transaction runs as the least-privileged RLS role. This is local to the transaction and cannot leak through pooling.
            await session.execute(text('SET LOCAL ROLE authenticated'))
            yield session
            await session.commit()
        except Exception:
            await session.rollback(); raise

@asynccontextmanager
async def system_session_context():
    """Internal worker context. Never expose this through request handlers; its DB role is privileged."""
    async with _session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback(); raise

async def tenant_session(organization_id:str)->AsyncGenerator[AsyncSession,None]:
    async with tenant_session_context(organization_id) as session: yield session

async def close_database()->None:
    global _engine,_sessions
    if _engine is not None: await _engine.dispose()
    _engine=None; _sessions=None
