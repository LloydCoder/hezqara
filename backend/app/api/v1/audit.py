from fastapi import APIRouter,Depends,Query
from sqlalchemy import text
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
router=APIRouter(prefix='/audit',tags=['audit'])
@router.get('')
async def list_audit(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission('audit:read'))):
    async with tenant_session_context(tenant.organization_id) as session:
        result=await session.execute(text("""select event_type,actor_id,resource_type,resource_id,request_id,outcome,action,created_at from audit_log
          where clinic_id=(select id from clinics where clerk_org_id=current_setting('app.clerk_org_id',true))
          order by created_at desc,id desc limit :limit offset :offset"""),{'limit':limit,'offset':offset})
        return [dict(r._mapping) for r in result]
