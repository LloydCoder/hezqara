from fastapi import APIRouter,Depends
from pydantic import BaseModel,Field
from sqlalchemy import text
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
router=APIRouter(prefix='/compliance',tags=['compliance'])
class ControlUpsert(BaseModel):
 framework:str=Field(min_length=2,max_length=80);control_key:str=Field(min_length=2,max_length=120);title:str=Field(min_length=2,max_length=300);status:str='planned';owner:str|None=None;evidence_ref:str|None=None;notes:str|None=None
@router.get('/controls')
async def list_controls(framework:str|None=None,tenant:TenantContext=Depends(require_permission('security:read'))):
 async with tenant_session_context(tenant.organization_id) as s:
  rows=await s.execute(text("SELECT id,framework,control_key,title,status,owner,evidence_ref,last_reviewed_at,notes FROM compliance_controls WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND (:framework IS NULL OR framework=:framework) ORDER BY framework,control_key"),{'framework':framework})
  return [dict(r) for r in rows.mappings()]
@router.post('/controls',status_code=201)
async def upsert_control(data:ControlUpsert,tenant:TenantContext=Depends(require_permission('security:manage'))):
 if data.status not in {'planned','implemented','evidenced','exception'}: raise ValueError('invalid control status')
 async with tenant_session_context(tenant.organization_id) as s:
  clinic=(await s.execute(text("SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)"))).scalar_one()
  row=(await s.execute(text("""INSERT INTO compliance_controls(clinic_id,framework,control_key,title,status,owner,evidence_ref,last_reviewed_at,notes) VALUES(:clinic,:framework,:key,:title,:status,:owner,:evidence,NOW(),:notes) ON CONFLICT(clinic_id,framework,control_key) DO UPDATE SET title=excluded.title,status=excluded.status,owner=excluded.owner,evidence_ref=excluded.evidence,last_reviewed_at=NOW(),notes=excluded.notes,updated_at=NOW() RETURNING id,framework,control_key,title,status,owner,evidence_ref,last_reviewed_at,notes"""),{'clinic':clinic,'framework':data.framework,'key':data.control_key,'title':data.title,'status':data.status,'owner':data.owner,'evidence':data.evidence_ref,'notes':data.notes})).mappings().one()
  return dict(row)
