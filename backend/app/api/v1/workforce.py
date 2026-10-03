from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy import text
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event
router=APIRouter(prefix='/workforce',tags=['unified-workforce'])
class WorkforceStart(BaseModel):
 workforce_key:str=Field(min_length=2,max_length=100)
 context:dict=dict()
 idempotency_key:str=Field(min_length=8,max_length=200)
@router.post('/runs',status_code=201)
async def start(data:WorkforceStart,request:Request,tenant:TenantContext=Depends(require_permission('workflow:execute'))):
 async with tenant_session_context(tenant.organization_id) as s:
  row=(await s.execute(text("""INSERT INTO workforce_runs(clinic_id,workforce_key,context,idempotency_key,status,current_stage) SELECT c.id,:workforce_key,:context::jsonb,:idempotency_key,'queued','reception' FROM clinics c WHERE c.clerk_org_id=current_setting('app.clerk_org_id',true) ON CONFLICT(clinic_id,idempotency_key) DO UPDATE SET updated_at=workforce_runs.updated_at RETURNING id,workforce_key,status,current_stage,context,idempotency_key,created_at,updated_at"""),{**data.model_dump(),'context':__import__('json').dumps(data.context)})).mappings().first()
  if not row: raise HTTPException(403,'clinic not provisioned')
  await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,action='workforce.run_started',resource_type='workforce_run',resource_id=row['id'],outcome=row['status'],request_id=getattr(request.state,'request_id',None))
  return dict(row)
@router.get('/runs/{run_id}')
async def get(run_id:str,tenant:TenantContext=Depends(require_permission('workflow:read'))):
 async with tenant_session_context(tenant.organization_id) as s:
  row=(await s.execute(text("SELECT id,workforce_key,status,context,current_stage,approval_required,failure_class,created_at,updated_at,started_at,completed_at FROM workforce_runs WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id"),{'id':run_id})).mappings().first()
  if not row: raise HTTPException(404,'workforce run not found')
  return dict(row)
