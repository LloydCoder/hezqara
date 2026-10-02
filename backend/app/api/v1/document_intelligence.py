from datetime import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event

router=APIRouter(prefix="/documents",tags=["document-intelligence"])

class IntakeCreate(BaseModel):
    patient_id:str|None=None
    source:str
    external_reference:str|None=None
    filename:str|None=None
    mime_type:str|None=None
    content_hash:str|None=None
    classification:str|None=None
    confidence:float|None=Field(default=None,ge=0,le=1)
    extracted:dict=Field(default_factory=dict)
    provenance:dict=Field(default_factory=dict)

class RouteCreate(BaseModel):
    target_type:str
    target_id:str|None=None
    reason:str|None=None

class ExtractionCreate(BaseModel):
    field_name:str
    value:object
    confidence:float|None=Field(default=None,ge=0,le=1)
    source_ref:str|None=None
    extractor_version:str|None=None

ALLOWED_ROUTE_TARGETS={"patient_record","authorization","referral","claim","task","review_queue"}

@router.post("/intake",status_code=201)
async def create_intake(data:IntakeCreate,request:Request,tenant:TenantContext=Depends(require_permission("records:write"))):
    if data.source not in {"fax","email","upload","ehr","api"}: raise HTTPException(422,"invalid document source")
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            INSERT INTO document_intake_items
              (clinic_id,patient_id,source,external_reference,filename,mime_type,content_hash,status,classification,confidence,extracted,provenance)
            SELECT c.id,:patient_id,:source,:external_reference,:filename,:mime_type,:content_hash,
                   CASE WHEN :patient_id IS NULL THEN 'needs_match' ELSE 'matched' END,
                   :classification,:confidence,:extracted::jsonb,:provenance::jsonb
            FROM clinics c
            WHERE c.clerk_org_id=current_setting('app.clerk_org_id',true)
              AND (:patient_id IS NULL OR EXISTS (SELECT 1 FROM patients p WHERE p.id=:patient_id AND p.clinic_id=c.id))
            ON CONFLICT (clinic_id,content_hash) DO UPDATE SET updated_at=document_intake_items.updated_at
            RETURNING id,patient_id,source,external_reference,filename,mime_type,content_hash,status,classification,confidence,
                      extracted,provenance,received_at,created_at,updated_at
        """),{**data.model_dump(),"extracted":json.dumps(data.extracted),"provenance":json.dumps(data.provenance)})).mappings().first()
        if not row: raise HTTPException(404,"patient not found")
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="document.intake_created",resource_type="document_intake_item",
                           resource_id=row["id"],outcome=row["status"],request_id=getattr(request.state,"request_id",None))
        return dict(row)

@router.get("/intake")
async def list_intake(status:str|None=None,patient_id:str|None=None,limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission("records:read"))):
    async with tenant_session_context(tenant.organization_id) as s:
        rows=await s.execute(text("""
            SELECT id,patient_id,source,external_reference,filename,mime_type,status,classification,confidence,
                   extracted,provenance,received_at,created_at,updated_at
            FROM document_intake_items
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND (:status IS NULL OR status=:status)
              AND (:patient_id IS NULL OR patient_id=:patient_id)
            ORDER BY received_at DESC LIMIT :limit OFFSET :offset
        """),{"status":status,"patient_id":patient_id,"limit":limit,"offset":offset})
        return [dict(r) for r in rows.mappings()]

@router.post("/intake/{intake_id}/route",status_code=201)
async def route_document(intake_id:str,data:RouteCreate,request:Request,tenant:TenantContext=Depends(require_permission("records:write"))):
    if data.target_type not in ALLOWED_ROUTE_TARGETS: raise HTTPException(422,"invalid route target")
    async with tenant_session_context(tenant.organization_id) as s:
        item=(await s.execute(text("""
            SELECT id,status FROM document_intake_items
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id FOR UPDATE
        """),{"id":intake_id})).mappings().first()
        if not item: raise HTTPException(404,"intake item not found")
        if item["status"] not in {"matched","classified","review_required","received"}:
            raise HTTPException(409,"document is not routeable in its current state")
        route=(await s.execute(text("""
            INSERT INTO document_routes(clinic_id,intake_id,target_type,target_id,reason,status,created_by)
            VALUES ((SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)),:intake_id,:target_type,:target_id,:reason,'routed',:actor)
            RETURNING id,intake_id,target_type,target_id,reason,status,created_at,updated_at
        """),{**data.model_dump(),"intake_id":intake_id,"actor":tenant.user_id})).mappings().one()
        await s.execute(text("""
            UPDATE document_intake_items SET status='routed',updated_at=NOW()
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id
        """),{"id":intake_id})
        return dict(route)

@router.post("/intake/{intake_id}/extractions",status_code=201)
async def add_extraction(intake_id:str,data:ExtractionCreate,request:Request,tenant:TenantContext=Depends(require_permission("records:write"))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            INSERT INTO document_extractions(clinic_id,intake_id,field_name,value,confidence,source_ref,extractor_version)
            SELECT (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)),:intake_id,:field_name,:value::jsonb,
                   :confidence,:source_ref,:extractor_version
            WHERE EXISTS (SELECT 1 FROM document_intake_items d WHERE d.id=:intake_id AND d.clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
            RETURNING id,intake_id,field_name,value,confidence,source_ref,extractor_version,created_at
        """),{**data.model_dump(),"intake_id":intake_id,"value":json.dumps(data.value)})).mappings().first()
        if not row: raise HTTPException(404,"intake item not found")
        return dict(row)

@router.post("/intake/{intake_id}/review")
async def review_document(intake_id:str,approved:bool,request:Request,tenant:TenantContext=Depends(require_permission("records:write"))):
    status="completed" if approved else "review_required"
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            UPDATE document_intake_items SET status=:status,updated_at=NOW()
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id
            RETURNING id,status,updated_at
        """),{"id":intake_id,"status":status})).mappings().first()
        if not row: raise HTTPException(404,"intake item not found")
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="document.reviewed",resource_type="document_intake_item",resource_id=intake_id,
                           outcome=status,request_id=getattr(request.state,"request_id",None))
        return dict(row)

@router.get("/referrals")
async def list_referrals(status:str|None=None,limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission("referrals:read"))):
    async with tenant_session_context(tenant.organization_id) as s:
        rows=await s.execute(text("""
            SELECT id,patient_id,destination,service,status,authorization_id,expires_at,last_follow_up_at,created_at,updated_at
            FROM referrals_v2
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND (:status IS NULL OR status=:status)
            ORDER BY updated_at DESC LIMIT :limit OFFSET :offset
        """),{"status":status,"limit":limit,"offset":offset})
        return [dict(r) for r in rows.mappings()]

@router.post("/referrals/{referral_id}/transition")
async def transition_referral(referral_id:str,status:str,reason:str|None=None,request:Request=None,tenant:TenantContext=Depends(require_permission("referrals:write"))):
    allowed={
      "draft":{"pending_review","cancelled"},"pending_review":{"ready","cancelled"},
      "ready":{"sent","cancelled"},"sent":{"received","cancelled"},"received":{"accepted","cancelled"},
      "accepted":{"scheduled","cancelled"},"scheduled":{"completed","cancelled"},
      "completed":set(),"expired":set(),"cancelled":set()
    }
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            SELECT id,status FROM referrals_v2
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id FOR UPDATE
        """),{"id":referral_id})).mappings().first()
        if not row: raise HTTPException(404,"referral not found")
        if status not in allowed.get(row["status"],set()):
            if status==row["status"]: return dict(row)
            raise HTTPException(409,f"invalid referral transition: {row['status']} -> {status}")
        updated=(await s.execute(text("""
            UPDATE referrals_v2 SET status=:status,last_follow_up_at=CASE WHEN :status IN ('sent','received') THEN NOW() ELSE last_follow_up_at END,updated_at=NOW()
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id
            RETURNING id,patient_id,destination,service,status,authorization_id,expires_at,last_follow_up_at,created_at,updated_at
        """),{"id":referral_id,"status":status})).mappings().one()
        await s.execute(text("""
            INSERT INTO referral_events(clinic_id,referral_id,from_status,to_status,actor,reason)
            SELECT clinic_id,id,:from_status,:to_status,:actor,:reason FROM referrals_v2 WHERE id=:id
        """),{"id":referral_id,"from_status":row["status"],"to_status":status,"actor":tenant.user_id,"reason":reason})
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="referral.transitioned",resource_type="referral",resource_id=referral_id,
                           outcome=status,request_id=getattr(request.state,"request_id",None) if request else None)
        return dict(updated)
