from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import text
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
router=APIRouter(prefix='/reliability',tags=['reliability'])
class Target(BaseModel):
 service_key:str=Field(min_length=2,max_length=100);slo_target:float=Field(gt=0,le=1);rto_seconds:int=Field(gt=0);rpo_seconds:int=Field(ge=0);max_concurrency:int|None=Field(None,gt=0);evidence_ref:str|None=None
@router.get('/targets')
async def list_targets(tenant:TenantContext=Depends(require_permission('reliability:read'))):
 async with tenant_session_context(tenant.organization_id) as s:
  rows=await s.execute(text("SELECT id,service_key,slo_target,rto_seconds,rpo_seconds,max_concurrency,status,evidence_ref,last_tested_at FROM reliability_targets WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) ORDER BY service_key"));return [dict(r) for r in rows.mappings()]
@router.post('/targets',status_code=201)
async def set_target(data:Target,tenant:TenantContext=Depends(require_permission('reliability:manage'))):
 async with tenant_session_context(tenant.organization_id) as s:
  clinic=(await s.execute(text("SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)"))).scalar_one()
  row=(await s.execute(text("""INSERT INTO reliability_targets(clinic_id,service_key,slo_target,rto_seconds,rpo_seconds,max_concurrency,evidence_ref) VALUES(:clinic,:service,:slo,:rto,:rpo,:concurrency,:evidence) ON CONFLICT(clinic_id,service_key) DO UPDATE SET slo_target=excluded.slo_target,rto_seconds=excluded.rto_seconds,rpo_seconds=excluded.rpo_seconds,max_concurrency=excluded.max_concurrency,evidence_ref=excluded.evidence,updated_at=NOW() RETURNING id,service_key,slo_target,rto_seconds,rpo_seconds,max_concurrency,status,evidence_ref"""),{'clinic':clinic,'service':data.service_key,'slo':data.slo_target,'rto':data.rto_seconds,'rpo':data.rpo_seconds,'concurrency':data.max_concurrency,'evidence':data.evidence_ref})).mappings().one();return dict(row)
@router.post('/targets/{target_id}/validate')
async def validate(target_id:str,tenant:TenantContext=Depends(require_permission('reliability:manage'))):
 async with tenant_session_context(tenant.organization_id) as s:
  row=(await s.execute(text("UPDATE reliability_targets SET status='validated',last_tested_at=NOW(),updated_at=NOW() WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id RETURNING id,status,last_tested_at"),{'id':target_id})).mappings().first()
  if not row:raise HTTPException(404,'reliability target not found')
  return dict(row)
