from fastapi import APIRouter,Depends
from pydantic import BaseModel,Field
from sqlalchemy import text
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
router=APIRouter(prefix='/commercial',tags=['commercial'])
class Plan(BaseModel):
 plan_key:str=Field(min_length=2,max_length=80);monthly_price_cents:int=Field(ge=0);included_providers:int=Field(gt=0);included_encounters:int|None=Field(None,ge=0);included_scribe_minutes:int|None=Field(None,ge=0)
class Gate(BaseModel):
 gate_key:str=Field(min_length=2,max_length=120);status:str='blocked';evidence_ref:str|None=None;owner:str|None=None;notes:str|None=None
@router.get('/plans')
async def plans(tenant:TenantContext=Depends(require_permission('commercial:read'))):
 async with tenant_session_context(tenant.organization_id) as s:
  rows=await s.execute(text("SELECT id,plan_key,monthly_price_cents,included_providers,included_encounters,included_scribe_minutes,status FROM commercial_plans WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) ORDER BY monthly_price_cents"));return [dict(r) for r in rows.mappings()]
@router.post('/plans',status_code=201)
async def create_plan(data:Plan,tenant:TenantContext=Depends(require_permission('commercial:manage'))):
 async with tenant_session_context(tenant.organization_id) as s:
  clinic=(await s.execute(text("SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)"))).scalar_one();row=(await s.execute(text("""INSERT INTO commercial_plans(clinic_id,plan_key,monthly_price_cents,included_providers,included_encounters,included_scribe_minutes) VALUES(:clinic,:key,:price,:providers,:encounters,:scribe) ON CONFLICT(clinic_id,plan_key) DO UPDATE SET monthly_price_cents=excluded.monthly_price_cents,included_providers=excluded.included_providers,included_encounters=excluded.included_encounters,included_scribe_minutes=excluded.included_scribe_minutes,updated_at=NOW() RETURNING id,plan_key,monthly_price_cents,included_providers,included_encounters,included_scribe_minutes,status"""),{'clinic':clinic,'key':data.plan_key,'price':data.monthly_price_cents,'providers':data.included_providers,'encounters':data.included_encounters,'scribe':data.included_scribe_minutes})).mappings().one();return dict(row)
@router.get('/launch-gates')
async def launch_gates(tenant:TenantContext=Depends(require_permission('commercial:read'))):
 async with tenant_session_context(tenant.organization_id) as s:
  rows=await s.execute(text("SELECT id,gate_key,status,evidence_ref,owner,notes,updated_at FROM launch_gates WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) ORDER BY gate_key"));return [dict(r) for r in rows.mappings()]
@router.post('/launch-gates',status_code=201)
async def set_gate(data:Gate,tenant:TenantContext=Depends(require_permission('commercial:manage'))):
 if data.status not in {'blocked','ready','waived'}:raise ValueError('invalid gate status')
 async with tenant_session_context(tenant.organization_id) as s:
  clinic=(await s.execute(text("SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)"))).scalar_one();row=(await s.execute(text("""INSERT INTO launch_gates(clinic_id,gate_key,status,evidence_ref,owner,notes) VALUES(:clinic,:key,:status,:evidence,:owner,:notes) ON CONFLICT(clinic_id,gate_key) DO UPDATE SET status=excluded.status,evidence_ref=excluded.evidence_ref,owner=excluded.owner,notes=excluded.notes,updated_at=NOW() RETURNING id,gate_key,status,evidence_ref,owner,notes,updated_at"""),{'clinic':clinic,'key':data.gate_key,'status':data.status,'evidence':data.evidence_ref,'owner':data.owner,'notes':data.notes})).mappings().one();return dict(row)
