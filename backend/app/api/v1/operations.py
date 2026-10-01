from fastapi import APIRouter,Depends
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.domains.operations.repository import OperationsRepository
from app.platform.reliability import operational_snapshot,readiness
router=APIRouter(prefix='/operations',tags=['operations'])

@router.get('/summary')
async def summary(tenant:TenantContext=Depends(require_permission('analytics:read'))):
 async with tenant_session_context(tenant.organization_id) as session:return await OperationsRepository(session).summary()

@router.get('/readiness')
async def production_readiness(tenant:TenantContext=Depends(require_permission('analytics:read'))):
 async with tenant_session_context(tenant.organization_id) as session:return await readiness(session)

@router.get('/operational-snapshot')
async def operational_state(tenant:TenantContext=Depends(require_permission('analytics:read'))):
 async with tenant_session_context(tenant.organization_id) as session:return await operational_snapshot(session,tenant.organization_id)
