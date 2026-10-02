from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event
from app.core.config import settings
from app.domains.insurance.engine import EligibilityRequest, build_eligibility_provider
from app.domains.insurance.fhir import coverage_resource, eligibility_request_resource, eligibility_response_resource, authorization_task_resource

router=APIRouter(prefix="/insurance",tags=["insurance-authorization"])

class EligibilityCreateV2(BaseModel):
    patient_id:str
    coverage_id:str|None=None
    payer_name:str=Field(min_length=1,max_length=200)
    member_id:str=Field(min_length=1,max_length=200)
    service_code:str|None=None
    idempotency_key:str=Field(min_length=8,max_length=200)

class BenefitCreate(BaseModel):
    coverage_id:str
    service_code:str|None=None
    category:str=Field(min_length=1,max_length=200)
    in_network:bool|None=None
    copay:float|None=None
    coinsurance_percent:float|None=Field(default=None,ge=0,le=100)
    deductible_remaining:float|None=None
    out_of_pocket_remaining:float|None=None
    notes:str|None=None
    effective_date:date|None=None
    termination_date:date|None=None

class AuthorizationCreateV2(BaseModel):
    patient_id:str
    payer_name:str=Field(min_length=1,max_length=200)
    service_code:str=Field(min_length=1,max_length=100)
    requested_date:date|None=None
    coverage_id:str|None=None
    documentation_required:list[str]=Field(default_factory=list)
    idempotency_key:str=Field(min_length=8,max_length=200)

class AuthorizationTransition(BaseModel):
    status:str
    reason:str|None=None

class AuthorizationDocumentCreate(BaseModel):
    document_type:str=Field(min_length=1,max_length=200)
    record_id:str|None=None
    required:bool=True
    provenance:dict=Field(default_factory=dict)

ALLOWED={
    "draft":{"ready_for_review","cancelled"},
    "ready_for_review":{"approved_for_submission","cancelled"},
    "approved_for_submission":{"submitted","cancelled"},
    "submitted":{"pending","additional_information_required","approved","denied"},
    "pending":{"additional_information_required","approved","denied","expired","cancelled"},
    "additional_information_required":{"ready_for_review","cancelled"},
    "approved":{"expired","cancelled"},
    "denied":set(),"expired":set(),"cancelled":set(),
}

@router.post("/eligibility",status_code=201)
async def check_eligibility_v2(data:EligibilityCreateV2,request:Request,tenant:TenantContext=Depends(require_permission("eligibility:write"))):
    provider=build_eligibility_provider(app_env=settings.app_env,configured=False)
    result=await provider.check(EligibilityRequest(
        data.patient_id,data.payer_name,data.member_id,data.service_code,getattr(request.state,"request_id",None)
    ))
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            INSERT INTO eligibility_requests
              (clinic_id,patient_id,coverage_id,payer_name,status,provider,provider_reference,response,idempotency_key,correlation_id,responded_at)
            SELECT c.id,:patient_id,:coverage_id,:payer_name,:status,:provider,:provider_reference,
                   :response::jsonb,:idempotency_key,:correlation_id,NOW()
            FROM clinics c
            WHERE c.clerk_org_id=current_setting('app.clerk_org_id',true)
              AND EXISTS (SELECT 1 FROM patients p WHERE p.id=:patient_id AND p.clinic_id=c.id)
              AND (:coverage_id IS NULL OR EXISTS
                   (SELECT 1 FROM patient_coverages pc WHERE pc.id=:coverage_id AND pc.clinic_id=c.id AND pc.patient_id=:patient_id))
            ON CONFLICT (clinic_id,idempotency_key) DO UPDATE SET id=eligibility_requests.id
            RETURNING id,patient_id,coverage_id,payer_name,status,provider,provider_reference,response,
                      requested_at,responded_at,benefits
        """),{
            **data.model_dump(),"status":result.status,"provider":result.provider,
            "provider_reference":result.provider_reference,
            "response":__import__("json").dumps({"reason":result.reason} if result.reason else {}),
            "correlation_id":getattr(request.state,"request_id",None)
        })).mappings().first()
        if not row: raise HTTPException(404,"patient or coverage not found")
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="eligibility.checked",resource_type="eligibility_request",
                           resource_id=row["id"],outcome=row["status"],request_id=getattr(request.state,"request_id",None))
        return dict(row)

@router.get("/benefits")
async def list_benefits(coverage_id:str,tenant:TenantContext=Depends(require_permission("insurance:read"))):
    async with tenant_session_context(tenant.organization_id) as s:
        rows=await s.execute(text("""
            SELECT id,coverage_id,service_code,category,in_network,copay,coinsurance_percent,
                   deductible_remaining,out_of_pocket_remaining,notes,effective_date,termination_date,
                   source,last_verified_at,created_at,updated_at
            FROM coverage_benefits WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND coverage_id=:coverage_id ORDER BY category,service_code
        """),{"coverage_id":coverage_id})
        return [dict(r) for r in rows.mappings()]

@router.post("/benefits",status_code=201)
async def create_benefit(data:BenefitCreate,request:Request,tenant:TenantContext=Depends(require_permission("insurance:write"))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            INSERT INTO coverage_benefits
              (clinic_id,coverage_id,service_code,category,in_network,copay,coinsurance_percent,
               deductible_remaining,out_of_pocket_remaining,notes,effective_date,termination_date)
            SELECT c.id,:coverage_id,:service_code,:category,:in_network,:copay,:coinsurance_percent,
                   :deductible_remaining,:out_of_pocket_remaining,:notes,:effective_date,:termination_date
            FROM clinics c JOIN patient_coverages pc ON pc.clinic_id=c.id
            WHERE c.clerk_org_id=current_setting('app.clerk_org_id',true) AND pc.id=:coverage_id
            ON CONFLICT (clinic_id,coverage_id,service_code,category)
            DO UPDATE SET in_network=EXCLUDED.in_network,copay=EXCLUDED.copay,
              coinsurance_percent=EXCLUDED.coinsurance_percent,deductible_remaining=EXCLUDED.deductible_remaining,
              out_of_pocket_remaining=EXCLUDED.out_of_pocket_remaining,notes=EXCLUDED.notes,
              updated_at=NOW()
            RETURNING *
        """),data.model_dump())).mappings().first()
        if not row: raise HTTPException(404,"coverage not found")
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="insurance.benefit_created",resource_type="coverage_benefit",
                           resource_id=row["id"],outcome="success",request_id=getattr(request.state,"request_id",None))
        return dict(row)

@router.post("/authorizations",status_code=201)
async def create_authorization(data:AuthorizationCreateV2,request:Request,tenant:TenantContext=Depends(require_permission("authorization:write"))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            INSERT INTO authorizations
              (clinic_id,patient_id,coverage_id,payer_name,service_code,requested_date,
               documentation_required,idempotency_key)
            SELECT c.id,:patient_id,:coverage_id,:payer_name,:service_code,:requested_date,
                   :documentation_required,:idempotency_key
            FROM clinics c
            WHERE c.clerk_org_id=current_setting('app.clerk_org_id',true)
              AND EXISTS (SELECT 1 FROM patients p WHERE p.id=:patient_id AND p.clinic_id=c.id)
              AND (:coverage_id IS NULL OR EXISTS
                   (SELECT 1 FROM patient_coverages pc WHERE pc.id=:coverage_id AND pc.clinic_id=c.id AND pc.patient_id=:patient_id))
            ON CONFLICT (clinic_id,idempotency_key) DO UPDATE SET updated_at=authorizations.updated_at
            RETURNING id,patient_id,coverage_id,payer_name,service_code,requested_date,status,
                      documentation_required,payer_reference,pending_reason,denial_reason,
                      submitted_at,response_at,expires_at,created_at,updated_at
        """),{**data.model_dump()})).mappings().first()
        if not row: raise HTTPException(404,"patient or coverage not found")
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="authorization.created",resource_type="authorization",
                           resource_id=row["id"],outcome=row["status"],request_id=getattr(request.state,"request_id",None))
        return dict(row)

@router.get("/authorizations")
async def list_authorizations(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission("authorization:read"))):
    async with tenant_session_context(tenant.organization_id) as s:
        rows=await s.execute(text("""
            SELECT id,patient_id,coverage_id,payer_name,service_code,requested_date,status,
                   documentation_required,payer_reference,pending_reason,denial_reason,submitted_at,
                   response_at,expires_at,created_at,updated_at
            FROM authorizations
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
            ORDER BY updated_at DESC,id DESC LIMIT :limit OFFSET :offset
        """),{"limit":limit,"offset":offset})
        return [dict(r) for r in rows.mappings()]

@router.post("/authorizations/{authorization_id}/transition")
async def transition_authorization(authorization_id:str,data:AuthorizationTransition,request:Request,tenant:TenantContext=Depends(require_permission("authorization:write"))):
    if data.status not in ALLOWED: raise HTTPException(422,"unsupported authorization status")
    if data.status=="submitted" and "approvals:approve" not in tenant.permissions:
        raise HTTPException(403,"authorization submission requires approval permission")
    async with tenant_session_context(tenant.organization_id) as s:
        current=(await s.execute(text("""
            SELECT id,status FROM authorizations
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND id=:id FOR UPDATE
        """),{"id":authorization_id})).mappings().first()
        if not current: raise HTTPException(404,"authorization not found")
        if data.status not in ALLOWED.get(current["status"],set()):
            if current["status"]==data.status: return dict(current)
            raise HTTPException(409,f"invalid authorization transition: {current['status']} -> {data.status}")
        updated=(await s.execute(text("""
            UPDATE authorizations SET status=:status,
              submitted_at=CASE WHEN :status='submitted' THEN NOW() ELSE submitted_at END,
              response_at=CASE WHEN :status IN ('approved','denied') THEN NOW() ELSE response_at END,
              updated_at=NOW()
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND id=:id
            RETURNING id,patient_id,coverage_id,payer_name,service_code,requested_date,status,
                      documentation_required,payer_reference,pending_reason,denial_reason,
                      submitted_at,response_at,expires_at,created_at,updated_at
        """),{"id":authorization_id,"status":data.status})).mappings().one()
        await s.execute(text("""
            INSERT INTO authorization_events(clinic_id,authorization_id,from_status,to_status,actor,reason)
            SELECT clinic_id,id,:from_status,:to_status,:actor,:reason FROM authorizations
            WHERE id=:id
        """),{"id":authorization_id,"from_status":current["status"],"to_status":data.status,
               "actor":tenant.user_id,"reason":data.reason})
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="authorization.transitioned",resource_type="authorization",
                           resource_id=authorization_id,outcome=data.status,request_id=getattr(request.state,"request_id",None))
        return dict(updated)

@router.post("/authorizations/{authorization_id}/documents",status_code=201)
async def add_authorization_document(authorization_id:str,data:AuthorizationDocumentCreate,request:Request,tenant:TenantContext=Depends(require_permission("authorization:write"))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            INSERT INTO authorization_documents
              (clinic_id,authorization_id,record_id,document_type,required,status,provenance)
            SELECT clinic_id,id,:record_id,:document_type,:required,
                   CASE WHEN :record_id IS NULL THEN 'missing' ELSE 'received' END,:provenance::jsonb
            FROM authorizations
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND id=:authorization_id
            RETURNING *
        """),{**data.model_dump(exclude_none=False),"authorization_id":authorization_id,
              "provenance":__import__("json").dumps(data.provenance)})).mappings().first()
        if not row: raise HTTPException(404,"authorization not found")
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="authorization.document_added",resource_type="authorization_document",
                           resource_id=row["id"],outcome=row["status"],request_id=getattr(request.state,"request_id",None))
        return dict(row)

@router.get("/authorizations/{authorization_id}/documents")
async def list_authorization_documents(authorization_id:str,tenant:TenantContext=Depends(require_permission("authorization:read"))):
    async with tenant_session_context(tenant.organization_id) as s:
        rows=await s.execute(text("""
            SELECT id,authorization_id,record_id,document_type,required,status,provenance,reviewed_by,reviewed_at,created_at,updated_at
            FROM authorization_documents
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND authorization_id=:authorization_id ORDER BY created_at
        """),{"authorization_id":authorization_id})
        return [dict(r) for r in rows.mappings()]

@router.get("/fhir/Coverage/{coverage_id}")
async def fhir_coverage(coverage_id:str,tenant:TenantContext=Depends(require_permission("insurance:read"))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            SELECT id,patient_id,payer_name,plan_name,member_id,priority,status,effective_date,termination_date
            FROM patient_coverages WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id
        """),{"id":coverage_id})).mappings().first()
        if not row: raise HTTPException(404,"coverage not found")
        return coverage_resource(dict(row))

@router.get("/fhir/CoverageEligibilityRequest/{request_id}")
async def fhir_eligibility_request(request_id:str,tenant:TenantContext=Depends(require_permission("eligibility:read"))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            SELECT id,patient_id,coverage_id,payer_name,status,requested_at
            FROM eligibility_requests WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id
        """),{"id":request_id})).mappings().first()
        if not row: raise HTTPException(404,"eligibility request not found")
        return eligibility_request_resource(dict(row))

@router.get("/fhir/CoverageEligibilityResponse/{request_id}")
async def fhir_eligibility_response(request_id:str,tenant:TenantContext=Depends(require_permission("eligibility:read"))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            SELECT id,patient_id,coverage_id,payer_name,status FROM eligibility_requests
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id
        """),{"id":request_id})).mappings().first()
        if not row: raise HTTPException(404,"eligibility response not found")
        return eligibility_response_resource(dict(row))

@router.get("/fhir/Task/{authorization_id}")
async def fhir_authorization_task(authorization_id:str,tenant:TenantContext=Depends(require_permission("authorization:read"))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            SELECT id,patient_id,status,created_at FROM authorizations
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id
        """),{"id":authorization_id})).mappings().first()
        if not row: raise HTTPException(404,"authorization not found")
        return authorization_task_resource(dict(row))
