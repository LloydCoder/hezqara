import json
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event

router=APIRouter(prefix="/engagement",tags=["patient-engagement"])
class CareGapCreate(BaseModel):
 patient_id:str
 gap_code:str=Field(min_length=2,max_length=100)
 description:str=Field(min_length=1,max_length=1000)
 source_ref:str|None=None
 evidence:dict=dict()
class OutreachCreate(BaseModel):
 patient_id:str
 care_gap_id:str|None=None
 channel:str
 subject:str|None=None
 body:str=Field(min_length=1,max_length=10000)
 template_key:str|None=None
 reason:str=Field(min_length=1,max_length=500)
 idempotency_key:str=Field(min_length=8,max_length=200)
class OutreachReview(BaseModel):
 approved:bool

@router.post("/care-gaps",status_code=201)
async def create_care_gap(data:CareGapCreate,request:Request,tenant:TenantContext=Depends(require_permission("patient_engagement:write"))):
 async with tenant_session_context(tenant.organization_id) as s:
  row=(await s.execute(text("""INSERT INTO care_gaps(clinic_id,patient_id,gap_code,source_ref,description,evidence) SELECT c.id,:patient_id,:gap_code,:source_ref,:description,:evidence::jsonb FROM clinics c WHERE c.clerk_org_id=current_setting('app.clerk_org_id',true) AND EXISTS(SELECT 1 FROM patients p WHERE p.id=:patient_id AND p.clinic_id=c.id) RETURNING id,patient_id,gap_code,source_ref,description,status,evidence,created_at,updated_at"""),{**data.model_dump(),"evidence":json.dumps(data.evidence)})).mappings().first()
  if not row: raise HTTPException(404,"patient not found")
  await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,action="care_gap.created",resource_type="care_gap",resource_id=row["id"],outcome="open",request_id=getattr(request.state,"request_id",None))
  return dict(row)

@router.get("/care-gaps")
async def list_care_gaps(status:str|None=None,limit:int=Query(50,ge=1,le=100),tenant:TenantContext=Depends(require_permission("patient_engagement:read"))):
 async with tenant_session_context(tenant.organization_id) as s:
  rows=await s.execute(text("SELECT id,patient_id,gap_code,source_ref,description,status,evidence,created_at,updated_at FROM care_gaps WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND (:status IS NULL OR status=:status) ORDER BY updated_at DESC LIMIT :limit"),{"status":status,"limit":limit})
  return [dict(r) for r in rows.mappings()]

@router.post("/outreach",status_code=201)
async def propose_outreach(data:OutreachCreate,request:Request,tenant:TenantContext=Depends(require_permission("patient_engagement:write"))):
 if data.channel not in {"sms","email","whatsapp"}: raise HTTPException(422,"invalid outreach channel")
 async with tenant_session_context(tenant.organization_id) as s:
  row=(await s.execute(text("""INSERT INTO outreach_proposals(clinic_id,patient_id,care_gap_id,channel,subject,body,template_key,reason,idempotency_key) SELECT c.id,:patient_id,:care_gap_id,:channel,:subject,:body,:template_key,:reason,:idempotency_key FROM clinics c WHERE c.clerk_org_id=current_setting('app.clerk_org_id',true) AND EXISTS(SELECT 1 FROM patients p WHERE p.id=:patient_id AND p.clinic_id=c.id) AND (:care_gap_id IS NULL OR EXISTS(SELECT 1 FROM care_gaps g WHERE g.id=:care_gap_id AND g.clinic_id=c.id)) ON CONFLICT (clinic_id,idempotency_key) DO UPDATE SET updated_at=outreach_proposals.updated_at RETURNING id,patient_id,care_gap_id,channel,subject,body,template_key,status,reason,idempotency_key,created_at,updated_at"""),data.model_dump())).mappings().first()
  if not row: raise HTTPException(404,"patient or care gap not found")
  await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,action="outreach.proposed",resource_type="outreach_proposal",resource_id=row["id"],outcome=row["status"],request_id=getattr(request.state,"request_id",None))
  return dict(row)

@router.post("/outreach/{proposal_id}/review")
async def review_outreach(proposal_id:str,data:OutreachReview,request:Request,tenant:TenantContext=Depends(require_permission("patient_engagement:approve"))):
 async with tenant_session_context(tenant.organization_id) as s:
  row=(await s.execute(text("UPDATE outreach_proposals SET status=:status,approved_by=:actor,approved_at=CASE WHEN :approved THEN NOW() ELSE approved_at END,updated_at=NOW() WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id AND status='proposed' RETURNING id,status,approved_by,approved_at"),{"id":proposal_id,"status":"approved" if data.approved else "cancelled","approved":data.approved,"actor":tenant.user_id})).mappings().first()
  if not row: raise HTTPException(404,"proposal not found or already reviewed")
  await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,action="outreach.reviewed",resource_type="outreach_proposal",resource_id=proposal_id,outcome=row["status"],request_id=getattr(request.state,"request_id",None))
  return dict(row)
