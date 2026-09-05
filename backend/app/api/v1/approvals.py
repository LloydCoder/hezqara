from datetime import datetime, timezone
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import text
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext

router=APIRouter(prefix='/approvals',tags=['approvals'])

@router.get('')
async def list_approvals(tenant:TenantContext=Depends(require_permission('approvals:read'))):
    async with tenant_session_context(tenant.organization_id) as session:
        rows=(await session.execute(text("select id,workflow_run_id,workflow_step_run_id,risk_level,status,requested_by,decided_by,expires_at,decided_at,created_at from workflow_approvals order by created_at desc,id desc limit 100"))).mappings()
        return [dict(row) for row in rows]

async def _decide(approval_id:str,tenant:TenantContext,status:str):
    run_id=None
    async with tenant_session_context(tenant.organization_id) as session:
        row=(await session.execute(text("select id,status,expires_at,workflow_run_id,workflow_step_run_id from workflow_approvals where id=:id and clinic_id in (select id from clinics where clerk_org_id=current_setting('app.clerk_org_id',true)) for update"),{'id':approval_id})).mappings().first()
        if not row: raise HTTPException(status_code=404,detail='approval not found')
        if row['status']!='pending': raise HTTPException(status_code=409,detail='approval is no longer pending')
        if row['expires_at'] and row['expires_at']<=datetime.now(timezone.utc):
            await session.execute(text("update workflow_approvals set status='expired' where id=:id"),{'id':approval_id}); raise HTTPException(status_code=409,detail='approval expired')
        await session.execute(text("update workflow_approvals set status=:status,decided_by=:actor,decided_at=now() where id=:id and status='pending'"),{'id':approval_id,'status':status,'actor':tenant.user_id})
        run_id=row['workflow_run_id']
        if status=='approved':
            await session.execute(text("update workflow_step_runs set status='queued' where id=:step and status='waiting_for_approval'"),{'step':row['workflow_step_run_id']})
        result=dict((await session.execute(text("select id,workflow_run_id,workflow_step_run_id,risk_level,status,requested_by,decided_by,expires_at,decided_at,created_at from workflow_approvals where id=:id"),{'id':approval_id})).mappings().first())
    if status=='approved' and run_id:
        from app.domains.workflows.runtime import execute_run
        try: await execute_run(tenant.organization_id,run_id)
        except Exception: pass
    return result

@router.post('/{approval_id}/approve')
async def approve(approval_id:str,tenant:TenantContext=Depends(require_permission('approvals:approve'))): return await _decide(approval_id,tenant,'approved')

@router.post('/{approval_id}/reject')
async def reject(approval_id:str,tenant:TenantContext=Depends(require_permission('approvals:approve'))): return await _decide(approval_id,tenant,'rejected')
