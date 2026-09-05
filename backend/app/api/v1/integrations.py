from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event
from app.integrations.testing.providers import TestAuthorizationProvider, TestClaimsProvider, TestEHRProvider, TestEligibilityProvider, TestFHIRProvider, TestMessagingProvider, TestPaymentProvider

router=APIRouter(prefix='/integrations',tags=['integrations'])
TEST_PROVIDERS={p.name:p for p in (TestFHIRProvider(),TestEHRProvider(),TestEligibilityProvider(),TestAuthorizationProvider(),TestClaimsProvider(),TestPaymentProvider(),TestMessagingProvider())}
class IntegrationCreate(BaseModel):
    name:str=Field(min_length=1,max_length=120); category:str=Field(min_length=1,max_length=60); provider_key:str=Field(min_length=1,max_length=80); api_version:str=Field(min_length=1,max_length=40); environment:str=Field(default='test',pattern='^(test|development|staging|production)$')

@router.get('')
async def list_integrations(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission('integrations:read'))):
    async with tenant_session_context(tenant.organization_id) as s:
        rows=(await s.execute(text('select id,name,category,provider_key,api_version,environment,status,enabled,created_at,updated_at from integrations order by name,id limit :limit offset :offset'),{'limit':limit,'offset':offset})).mappings(); return [dict(r) for r in rows]

@router.get('/capabilities')
async def capabilities(tenant:TenantContext=Depends(require_permission('integrations:read'))):
    async with tenant_session_context(tenant.organization_id) as s:
        rows=(await s.execute(text('select i.provider_key,c.capability,c.supported,c.version from integrations i join integration_capabilities c on c.integration_id=i.id order by i.provider_key,c.capability'))).mappings(); return [dict(r) for r in rows]

@router.post('',status_code=201)
async def create_integration(data:IntegrationCreate,request:Request,tenant:TenantContext=Depends(require_permission('integrations:manage'))):
    if data.environment=='production' and data.provider_key.startswith('test-'): raise HTTPException(422,'test provider cannot be configured for production')
    async with tenant_session_context(tenant.organization_id) as s:
        clinic=(await s.execute(text("select id from clinics where clerk_org_id=current_setting('app.clerk_org_id',true) limit 1"))).scalar()
        if not clinic: raise HTTPException(404,'tenant clinic not found')
        row=(await s.execute(text("insert into integrations(clinic_id,name,category,provider_key,api_version,environment,status) values(:clinic,:name,:category,:provider,:version,:environment,'not_configured') on conflict(clinic_id,provider_key) do update set name=excluded.name,api_version=excluded.api_version,environment=excluded.environment,updated_at=now() returning id,name,category,provider_key,api_version,environment,status,enabled,created_at,updated_at"),{'clinic':clinic,'name':data.name,'category':data.category,'provider':data.provider_key,'version':data.api_version,'environment':data.environment})).mappings().one()
        provider=TEST_PROVIDERS.get(data.provider_key)
        if provider:
            for capability,supported in provider.capabilities.__dict__.items():
                if isinstance(supported,bool): await s.execute(text("insert into integration_capabilities(clinic_id,integration_id,capability,supported,version) values(:clinic,:id,:cap,:supported,:version) on conflict(integration_id,capability) do update set supported=excluded.supported,version=excluded.version,clinic_id=excluded.clinic_id"),{'clinic':clinic,'id':row['id'],'cap':capability,'supported':supported,'version':provider.version})
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,action='integration.created',resource_type='integration',resource_id=str(row['id']),outcome='success',request_id=getattr(request.state,'request_id',None)); return dict(row)

@router.post('/{integration_id}/test-connection')
async def test_connection(integration_id:str,request:Request,tenant:TenantContext=Depends(require_permission('integrations:test'))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text('select id,provider_key,environment,status,clinic_id from integrations where id=:id'),{'id':integration_id})).mappings().first()
        if not row: raise HTTPException(404,'integration not found')
        provider=TEST_PROVIDERS.get(row['provider_key'])
        if not provider: return {'state':'configuration_required','message':'No configured production adapter is available for this provider.'}
        health=await provider.health()
        await s.execute(text('update integrations set status=:status,updated_at=now() where id=:id'),{'id':integration_id,'status':health.state})
        await s.execute(text('insert into integration_health(clinic_id,integration_id,state,latency_ms,error_code) values(:clinic,:id,:state,:latency,:error)'),{'clinic':row['clinic_id'],'id':integration_id,'state':health.state,'latency':health.latency_ms,'error':health.error.code if health.error else None})
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,action='integration.connection_tested',resource_type='integration',resource_id=integration_id,outcome=health.state,request_id=getattr(request.state,'request_id',None)); return {'state':health.state,'provider':provider.name,'version':provider.version,'checked_at':datetime.now(timezone.utc).isoformat()}

@router.get('/{integration_id}/health')
async def integration_health(integration_id:str,tenant:TenantContext=Depends(require_permission('integrations:read'))):
    async with tenant_session_context(tenant.organization_id) as s:
        rows=(await s.execute(text('select state,latency_ms,error_code,checked_at from integration_health where integration_id=:id order by checked_at desc limit 20'),{'id':integration_id})).mappings(); return [dict(r) for r in rows]

@router.get('/{integration_id}/activity')
async def integration_activity(integration_id:str,limit:int=Query(50,ge=1,le=100),tenant:TenantContext=Depends(require_permission('integrations:read'))):
    async with tenant_session_context(tenant.organization_id) as s:
        rows=(await s.execute(text('select id,operation,status,provider_status,external_reference,latency_ms,error_code,retry_count,created_at,completed_at from integration_requests where integration_id=:id order by created_at desc limit :limit'),{'id':integration_id,'limit':limit})).mappings(); return [dict(r) for r in rows]
