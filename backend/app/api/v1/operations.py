from fastapi import APIRouter,Depends
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.domains.operations.repository import OperationsRepository
router=APIRouter(prefix='/operations',tags=['operations'])
@router.get('/summary')
async def summary(tenant:TenantContext=Depends(require_permission('analytics:read'))):
 async with tenant_session_context(tenant.organization_id) as session:return await OperationsRepository(session).summary()
