from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy import text
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event
router=APIRouter(prefix='/interoperability',tags=['interoperability'])
class ConnectionCreate(BaseModel):
 provider_key:str=Field(min_length=2,max_length=100);interface_type:str;environment:str='sandbox';endpoint:str|None=None;auth_scheme:str|None=None;supported_resources:list[str]=[];metadata:dict={}
@router.get('/connections')
async def list_connections(tenant:TenantContext=Depends(require_permission('integrations:read'))):
 async with tenant_session_context(tenant.organization_id) as s:
  rows=await s.execute(text("SELECT id,provider_key,interface_type,environment,endpoint,auth_scheme,supported_resources,status,last_verified_at,failure_class,metadata FROM integration_connections WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) ORDER BY provider_key"))
  return [dict(r) for r in rows.mappings()]
@router.post('/connections',status_code=201)
async def register_connection(data:ConnectionCreate,request:Request,tenant:TenantContext=Depends(require_permission('integrations:manage'))):
 if data.interface_type not in {'fhir','smart','payer_api','payment','messaging','document'}:raise HTTPException(422,'invalid interface type')
 if data.environment not in {'sandbox','production'}:raise HTTPException(422,'invalid environment')
 async with tenant_session_context(tenant.organization_id) as s:
  clinic=(await s.execute(text("SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)"))).scalar_one_or_none()
  if not clinic:raise HTTPException(403,'clinic not provisioned')
  row=(await s.execute(text("""INSERT INTO integration_connections(clinic_id,provider_key,interface_type,environment,endpoint,auth_scheme,supported_resources,metadata) VALUES(:clinic,:provider,:interface,:environment,:endpoint,:auth,cast(:resources as jsonb),cast(:metadata as jsonb)) ON CONFLICT(clinic_id,provider_key,interface_type,environment) DO UPDATE SET endpoint=excluded.endpoint,auth_scheme=excluded.auth_scheme,supported_resources=excluded.supported_resources,metadata=excluded.metadata,updated_at=NOW() RETURNING id,provider_key,interface_type,environment,endpoint,auth_scheme,supported_resources,status,last_verified_at"""),{'clinic':clinic,'provider':data.provider_key,'interface':data.interface_type,'environment':data.environment,'endpoint':data.endpoint,'auth':data.auth_scheme,'resources':__import__('json').dumps(data.supported_resources),'metadata':__import__('json').dumps(data.metadata)})).mappings().one()
  await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,action='integration.connection.registered',resource_type='integration_connection',resource_id=row['id'],outcome='registered',request_id=getattr(request.state,'request_id',None));return dict(row)
@router.post('/connections/{connection_id}/verify')
async def verify_connection(connection_id:str,request:Request,tenant:TenantContext=Depends(require_permission('integrations:manage'))):
 async with tenant_session_context(tenant.organization_id) as s:
  row=(await s.execute(text("UPDATE integration_connections SET status=CASE WHEN endpoint IS NULL THEN 'failed' ELSE 'healthy' END,last_verified_at=NOW(),failure_class=CASE WHEN endpoint IS NULL THEN 'ENDPOINT_NOT_CONFIGURED' ELSE NULL END,updated_at=NOW() WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id RETURNING id,status,last_verified_at,failure_class"),{'id':connection_id})).mappings().first()
  if not row:raise HTTPException(404,'connection not found')
  await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,action='integration.connection.verified',resource_type='integration_connection',resource_id=connection_id,outcome=row['status'],request_id=getattr(request.state,'request_id',None));return dict(row)
