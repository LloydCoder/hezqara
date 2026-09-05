from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from app.core.config import settings
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event
from app.domains.claims.engine import validate_payment_state
from app.domains.claims.service import ClaimsService
from app.domains.insurance.engine import EligibilityRequest, build_eligibility_provider

router=APIRouter(prefix='/admin',tags=['healthcare-administration'])
class CoverageCreate(BaseModel):
    patient_id:str; payer_name:str=Field(min_length=1,max_length=200); plan_name:str|None=None; member_id:str=Field(min_length=1,max_length=200); priority:int=Field(default=1,ge=1); effective_date:date|None=None; termination_date:date|None=None
class EligibilityCreate(BaseModel):
    patient_id:str; coverage_id:str|None=None; payer_name:str=Field(min_length=1,max_length=200); member_id:str=Field(min_length=1,max_length=200); service_code:str|None=None; idempotency_key:str=Field(min_length=8,max_length=200)
class ClaimCreate(BaseModel):
    patient_id:str; payer_name:str=Field(min_length=1,max_length=200); billed_amount:Decimal=Field(ge=0); expected_amount:Decimal|None=Field(default=None,ge=0); coverage_id:str|None=None
class Transition(BaseModel): status:str
class PaymentState(BaseModel): status:str
class AuthorizationCreate(BaseModel):
    patient_id:str; payer_name:str=Field(min_length=1,max_length=200); service_code:str=Field(min_length=1,max_length=100); requested_date:date|None=None; coverage_id:str|None=None; documentation_required:list[str]=Field(default_factory=list)
class ReferralCreate(BaseModel):
    patient_id:str; destination:str=Field(min_length=1,max_length=300); service:str|None=None; referring_provider:str|None=None; receiving_provider:str|None=None; authorization_id:str|None=None

@router.get('/coverage')
async def list_coverage(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission('insurance:read'))):
    async with tenant_session_context(tenant.organization_id) as s:
        rows=await s.execute(text('select id,patient_id,payer_name,plan_name,member_id,priority,status,verification_state,last_verified_at,effective_date,termination_date,source,created_at,updated_at from patient_coverages order by priority,id limit :limit offset :offset'),{'limit':limit,'offset':offset}); return [dict(r) for r in rows.mappings()]

@router.post('/coverage',status_code=201)
async def create_coverage(data:CoverageCreate,request:Request,tenant:TenantContext=Depends(require_permission('insurance:write'))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("insert into patient_coverages(clinic_id,patient_id,payer_name,plan_name,member_id,priority,effective_date,termination_date) select c.id,:patient,:payer,:plan,:member,:priority,:effective,:termination from clinics c where c.clerk_org_id=current_setting('app.clerk_org_id',true) and exists(select 1 from patients p where p.id=:patient and p.clinic_id=c.id) returning id,patient_id,payer_name,plan_name,member_id,priority,status,verification_state,effective_date,termination_date,created_at,updated_at"),data.model_dump())).mappings().first()
        if not row: raise HTTPException(404,'patient not found')
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,action='coverage.created',resource_type='coverage',resource_id=row['id'],outcome='success',request_id=getattr(request.state,'request_id',None)); return dict(row)

@router.post('/eligibility',status_code=201)
async def check_eligibility(data:EligibilityCreate,request:Request,tenant:TenantContext=Depends(require_permission('eligibility:write'))):
    provider=build_eligibility_provider(app_env=settings.app_env,configured=False)
    result=await provider.check(EligibilityRequest(data.patient_id,data.payer_name,data.member_id,data.service_code,getattr(request.state,'request_id',None)))
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("insert into eligibility_requests(clinic_id,patient_id,coverage_id,payer_name,status,provider,response,idempotency_key,correlation_id,responded_at) select c.id,:patient,:coverage,:payer,:status,:provider,:response::jsonb,:key,:corr,now() from clinics c where c.clerk_org_id=current_setting('app.clerk_org_id',true) and exists(select 1 from patients p where p.id=:patient and p.clinic_id=c.id) and (:coverage is null or exists(select 1 from patient_coverages pc where pc.id=:coverage and pc.clinic_id=c.id and pc.patient_id=:patient)) on conflict(clinic_id,idempotency_key) do update set id=eligibility_requests.id returning id,status,provider,response,requested_at,responded_at"),{'patient':data.patient_id,'coverage':data.coverage_id,'payer':data.payer_name,'status':result.status,'provider':result.provider,'response':'{}','key':data.idempotency_key,'corr':getattr(request.state,'request_id',None)})).mappings().first()
        if not row: raise HTTPException(404,'patient or coverage not found')
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,action='eligibility.checked',resource_type='eligibility_request',resource_id=row['id'],outcome=result.status,request_id=getattr(request.state,'request_id',None)); return {**dict(row),'reason':result.reason}

@router.get('/claims')
async def list_claims(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission('claims:read'))):
    async with tenant_session_context(tenant.organization_id) as s:return await ClaimsService(s).list(limit,offset)

@router.post('/claims',status_code=201)
async def create_claim(data:ClaimCreate,request:Request,tenant:TenantContext=Depends(require_permission('claims:write'))):
    async with tenant_session_context(tenant.organization_id) as s:
        try: row=await ClaimsService(s).create(data.patient_id,data.payer_name,data.billed_amount,data.expected_amount,data.coverage_id)
        except ValueError as e: raise HTTPException(404,str(e)) from e
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,action='claim.created',resource_type='claim',resource_id=row['id'],outcome='success',request_id=getattr(request.state,'request_id',None)); return row

@router.post('/claims/{claim_id}/transition')
async def transition_claim(claim_id:str,data:Transition,request:Request,tenant:TenantContext=Depends(require_permission('claims:submit'))):
    if data.status=='submitted' and 'approvals:approve' not in tenant.permissions: raise HTTPException(403,'claim submission requires approval permission')
    async with tenant_session_context(tenant.organization_id) as s:
        try: row=await ClaimsService(s).transition(claim_id,data.status)
        except ValueError as e: raise HTTPException(409,str(e)) from e
        if not row: raise HTTPException(404,'claim not found')
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,action='claim.status_changed',resource_type='claim',resource_id=claim_id,outcome=data.status,request_id=getattr(request.state,'request_id',None)); return row

@router.post('/payments/{payment_id}/state')
async def payment_state(payment_id:str,data:PaymentState,tenant:TenantContext=Depends(require_permission('billing:write'))):
    try: validate_payment_state(data.status)
    except ValueError as e: raise HTTPException(422,str(e)) from e
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text('select id,status from billing_payments where id=:id for update'),{'id':payment_id})).mappings().first()
        if not row: raise HTTPException(404,'payment not found')
        if row['status']==data.status:return dict(row)
        allowed={'pending':{'authorized','failed','voided'},'authorized':{'paid','failed','voided'},'paid':{'refunded'},'failed':set(),'refunded':set(),'voided':set()}
        if data.status not in allowed.get(row['status'],set()): raise HTTPException(409,f"invalid payment transition: {row['status']} -> {data.status}")
        updated=(await s.execute(text('update billing_payments set status=:status,updated_at=now() where id=:id returning id,status,updated_at'),{'id':payment_id,'status':data.status})).mappings().first(); return dict(updated)

@router.post('/authorizations',status_code=201)
async def create_authorization(data:AuthorizationCreate,request:Request,tenant:TenantContext=Depends(require_permission('authorization:write'))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("insert into authorizations(clinic_id,patient_id,coverage_id,payer_name,service_code,requested_date,documentation_required) select c.id,:patient,:coverage,:payer,:service,:date,:docs from clinics c where c.clerk_org_id=current_setting('app.clerk_org_id',true) and exists(select 1 from patients p where p.id=:patient and p.clinic_id=c.id) and (:coverage is null or exists(select 1 from patient_coverages pc where pc.id=:coverage and pc.clinic_id=c.id and pc.patient_id=:patient)) returning id,patient_id,payer_name,service_code,requested_date,status,documentation_required,created_at,updated_at"),{'patient':data.patient_id,'coverage':data.coverage_id,'payer':data.payer_name,'service':data.service_code,'date':data.requested_date,'docs':data.documentation_required})).mappings().first()
        if not row: raise HTTPException(404,'patient or coverage not found')
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,action='authorization.created',resource_type='authorization',resource_id=row['id'],outcome='draft',request_id=getattr(request.state,'request_id',None)); return dict(row)

@router.get('/authorizations')
async def list_authorizations(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission('authorization:read'))):
    async with tenant_session_context(tenant.organization_id) as s:
        rows=await s.execute(text('select id,patient_id,payer_name,service_code,requested_date,status,payer_reference,pending_reason,denial_reason,submitted_at,response_at,expires_at,created_at,updated_at from authorizations order by updated_at desc,id desc limit :limit offset :offset'),{'limit':limit,'offset':offset}); return [dict(r) for r in rows.mappings()]

@router.get('/denials')
async def list_denials(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission('claims:read'))):
    async with tenant_session_context(tenant.organization_id) as s:
        rows=await s.execute(text('select id,claim_id,denial_code,category,payer_name,amount,received_at,deadline_at,status,owner_id,recommended_action,appeal_state,created_at,updated_at from denials order by deadline_at nulls last,created_at desc limit :limit offset :offset'),{'limit':limit,'offset':offset}); return [dict(r) for r in rows.mappings()]

@router.post('/referrals',status_code=201)
async def create_referral(data:ReferralCreate,request:Request,tenant:TenantContext=Depends(require_permission('referrals:write'))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("insert into referrals_v2(clinic_id,patient_id,referring_provider,receiving_provider,destination,service,authorization_id) select c.id,:patient,:referring,:receiving,:destination,:service,:auth from clinics c where c.clerk_org_id=current_setting('app.clerk_org_id',true) and exists(select 1 from patients p where p.id=:patient and p.clinic_id=c.id) and (:auth is null or exists(select 1 from authorizations a where a.id=:auth and a.clinic_id=c.id and a.patient_id=:patient)) returning id,patient_id,destination,service,status,authorization_id,created_at,updated_at"),data.model_dump())).mappings().first()
        if not row: raise HTTPException(404,'patient or authorization not found')
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,action='referral.created',resource_type='referral',resource_id=row['id'],outcome='draft',request_id=getattr(request.state,'request_id',None)); return dict(row)

@router.get('/referrals')
async def list_referrals(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission('referrals:read'))):
    async with tenant_session_context(tenant.organization_id) as s:
        rows=await s.execute(text('select id,patient_id,destination,service,status,authorization_id,expires_at,last_follow_up_at,created_at,updated_at from referrals_v2 order by updated_at desc,id desc limit :limit offset :offset'),{'limit':limit,'offset':offset}); return [dict(r) for r in rows.mappings()]

@router.get('/records')
async def list_records(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission('records:read'))):
    async with tenant_session_context(tenant.organization_id) as s:
        rows=await s.execute(text('select id,patient_id,document_type,source,received_at,status,required,retention_until,created_at,updated_at from records_v2 order by created_at desc,id desc limit :limit offset :offset'),{'limit':limit,'offset':offset}); return [dict(r) for r in rows.mappings()]

@router.get('/summary')
async def summary(tenant:TenantContext=Depends(require_permission('analytics:read'))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("select (select count(*) from patient_coverages where verification_state='pending_verification') verification_pending,(select count(*) from eligibility_requests where status in ('queued','submitted')) eligibility_pending,(select count(*) from authorizations where status in ('ready_for_review','submitted','pending','additional_information_required')) authorization_pending,(select count(*) from claims where status in ('ready','submitted','accepted','pending')) claims_pending,(select count(*) from claims where status='denied') denied_claims,(select coalesce(sum(amount),0) from ar_work_items where status not in ('resolved','closed')) ar_outstanding,(select count(*) from ar_work_items where status not in ('resolved','closed')) ar_work_items,(select count(*) from denials where status not in ('resolved','closed')) denial_queue"))).mappings().one()
        return dict(row)
