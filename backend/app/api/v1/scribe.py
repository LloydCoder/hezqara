import json
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from app.core.config import settings
from app.ai.providers.factory import build_provider
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event
from app.domains.scribe.speech import provider_contract

router=APIRouter(prefix="/scribe",tags=["ambient-clinical-documentation"])

class EncounterCreate(BaseModel):
    patient_id:str
    appointment_id:str|None=None
    clinician_id:str|None=None
    consent_status:str="unknown"
    audio_ref:str|None=None
    audio_retention_until:str|None=None

class TranscriptIngest(BaseModel):
    provider_name:str
    model_version:str
    transcript_text:str=Field(min_length=1)
    segments:list[dict]=Field(default_factory=list)
    language_code:str|None=None
    provider_request_id:str|None=None
    provenance:dict=Field(default_factory=dict)

class NoteEdit(BaseModel):
    note_text:str=Field(min_length=1)
    structured_note:dict=Field(default_factory=dict)

class DraftRequest(BaseModel):
    specialty:str="primary-care"
    template_version:str="e15.v1"

def _encounter_state(status):
    if status in {"approved","committed"}: return status
    return status

@router.get("/provider-contract")
async def speech_provider_contract(tenant:TenantContext=Depends(require_permission("clinical_documentation:read"))):
    return provider_contract()

@router.post("/encounters",status_code=201)
async def create_encounter(data:EncounterCreate,request:Request,tenant:TenantContext=Depends(require_permission("clinical_documentation:write"))):
    if data.consent_status not in {"unknown","obtained","declined","not_required"}:
        raise HTTPException(422,"invalid consent status")
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            INSERT INTO scribe_encounters(clinic_id,patient_id,appointment_id,clinician_id,consent_status,audio_ref,audio_retention_until)
            SELECT c.id,:patient_id,:appointment_id,:clinician_id,:consent_status,:audio_ref,:audio_retention_until::date
            FROM clinics c
            WHERE c.clerk_org_id=current_setting('app.clerk_org_id',true)
              AND EXISTS (SELECT 1 FROM patients p WHERE p.id=:patient_id AND p.clinic_id=c.id)
              AND (:appointment_id IS NULL OR EXISTS
                   (SELECT 1 FROM appointments a WHERE a.id=:appointment_id AND a.clinic_id=c.id AND a.patient_id=:patient_id))
            RETURNING id,patient_id,appointment_id,clinician_id,consent_status,status,audio_ref,audio_retention_until,created_at,updated_at
        """),data.model_dump())).mappings().first()
        if not row: raise HTTPException(404,"patient or appointment not found")
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="scribe.encounter_created",resource_type="scribe_encounter",
                           resource_id=row["id"],outcome="created",request_id=getattr(request.state,"request_id",None))
        return dict(row)

@router.post("/encounters/{encounter_id}/start")
async def start_encounter(encounter_id:str,request:Request,tenant:TenantContext=Depends(require_permission("clinical_documentation:write"))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            UPDATE scribe_encounters SET status='recording',started_at=COALESCE(started_at,NOW()),updated_at=NOW()
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND id=:id AND consent_status IN ('obtained','not_required') AND status='created'
            RETURNING id,status,started_at
        """),{"id":encounter_id})).mappings().first()
        if not row: raise HTTPException(409,"encounter is not consented or cannot be started")
        return dict(row)

@router.post("/encounters/{encounter_id}/stop")
async def stop_encounter(encounter_id:str,request:Request,tenant:TenantContext=Depends(require_permission("clinical_documentation:write"))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            UPDATE scribe_encounters SET status='transcribing',ended_at=COALESCE(ended_at,NOW()),updated_at=NOW()
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND id=:id AND status='recording'
            RETURNING id,status,ended_at,audio_ref
        """),{"id":encounter_id})).mappings().first()
        if not row: raise HTTPException(409,"encounter is not recording")
        return dict(row)

@router.post("/encounters/{encounter_id}/transcript",status_code=201)
async def ingest_transcript(encounter_id:str,data:TranscriptIngest,request:Request,tenant:TenantContext=Depends(require_permission("clinical_documentation:write"))):
    async with tenant_session_context(tenant.organization_id) as s:
        encounter=(await s.execute(text("""
            SELECT id,status FROM scribe_encounters
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id
        """),{"id":encounter_id})).mappings().first()
        if not encounter: raise HTTPException(404,"encounter not found")
        row=(await s.execute(text("""
            INSERT INTO scribe_transcripts(clinic_id,encounter_id,provider_name,model_version,language_code,
              transcript_text,segments,provider_request_id,provenance)
            VALUES ((SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)),:encounter_id,
              :provider_name,:model_version,:language_code,:transcript_text,:segments::jsonb,
              :provider_request_id,:provenance::jsonb)
            RETURNING id,encounter_id,provider_name,model_version,language_code,transcript_text,segments,
                      provider_request_id,provenance,created_at
        """),{**data.model_dump(),"encounter_id":encounter_id,"segments":json.dumps(data.segments),
              "provenance":json.dumps(data.provenance)})).mappings().one()
        await s.execute(text("""
            UPDATE scribe_encounters SET status='draft',updated_at=NOW()
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id
        """),{"id":encounter_id})
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="scribe.transcript_ingested",resource_type="scribe_transcript",
                           resource_id=row["id"],outcome="draft",request_id=getattr(request.state,"request_id",None),
                           metadata={"provider":data.provider_name,"model_version":data.model_version})
        return dict(row)

@router.post("/encounters/{encounter_id}/draft",status_code=201)
async def generate_draft(encounter_id:str,data:DraftRequest,request:Request,tenant:TenantContext=Depends(require_permission("clinical_documentation:write"))):
    async with tenant_session_context(tenant.organization_id) as s:
        source=(await s.execute(text("""
            SELECT t.id,t.transcript_text,t.segments,e.patient_id
            FROM scribe_transcripts t JOIN scribe_encounters e ON e.id=t.encounter_id AND e.clinic_id=t.clinic_id
            WHERE t.clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND t.encounter_id=:id ORDER BY t.created_at DESC LIMIT 1
        """),{"id":encounter_id})).mappings().first()
        if not source: raise HTTPException(404,"transcript not found")
        provider=build_provider()
        if provider is None: raise HTTPException(503,"no approved clinical documentation model provider is configured")
        schema={"type":"object","properties":{"note_text":{"type":"string"},"structured_note":{"type":"object"}},"required":["note_text","structured_note"]}
        system=f"You are a clinical documentation drafting assistant. Draft a faithful {data.specialty} encounter note from the transcript. Do not diagnose, invent findings, or add treatment recommendations not supported by the transcript. Mark uncertain or missing information explicitly. The clinician must review and approve the draft."
        result=await provider.structured_output(system_prompt=system,user_input=source["transcript_text"],model=settings.ai_model,schema=schema)
        note=(await s.execute(text("""
            INSERT INTO scribe_notes(clinic_id,encounter_id,transcript_id,template_version,model_version,note_text,structured_note,status)
            VALUES ((SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)),:encounter_id,:transcript_id,
                    :template_version,:model_version,:note_text,:structured_note::jsonb,'review')
            RETURNING id,encounter_id,transcript_id,template_version,model_version,note_text,structured_note,status,created_at,updated_at
        """),{"encounter_id":encounter_id,"transcript_id":source["id"],"template_version":data.template_version,
              "model_version":settings.ai_model,"note_text":result["note_text"],"structured_note":json.dumps(result["structured_note"])})).mappings().one()
        await s.execute(text("""
            INSERT INTO scribe_note_provenance(clinic_id,note_id,source_type,source_id,source_ref,excerpt)
            VALUES ((SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)),:note_id,'transcript',:source_id,:source_id,:excerpt)
        """),{"note_id":note["id"],"source_id":source["id"],"excerpt":source["transcript_text"][:1000]})
        return dict(note)

@router.patch("/notes/{note_id}")
async def edit_note(note_id:str,data:NoteEdit,request:Request,tenant:TenantContext=Depends(require_permission("clinical_documentation:write"))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            UPDATE scribe_notes SET note_text=:note_text,structured_note=:structured_note::jsonb,status='review',updated_at=NOW()
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND id=:id AND status IN ('draft','review')
            RETURNING id,note_text,structured_note,status,updated_at
        """),{"id":note_id,"note_text":data.note_text,"structured_note":json.dumps(data.structured_note)})).mappings().first()
        if not row: raise HTTPException(404,"editable note not found")
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="scribe.note_edited",resource_type="scribe_note",resource_id=note_id,
                           outcome="review",request_id=getattr(request.state,"request_id",None))
        return dict(row)

@router.post("/notes/{note_id}/approve")
async def approve_note(note_id:str,request:Request,tenant:TenantContext=Depends(require_permission("clinical_documentation:approve"))):
    if "approvals:approve" not in tenant.permissions: raise HTTPException(403,"clinician approval requires approval permission")
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            UPDATE scribe_notes SET status='approved',clinician_id=:clinician_id,approved_at=NOW(),updated_at=NOW()
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND id=:id AND status='review'
            RETURNING id,encounter_id,status,clinician_id,approved_at,updated_at
        """),{"id":note_id,"clinician_id":tenant.user_id})).mappings().first()
        if not row: raise HTTPException(409,"note is not awaiting clinician review")
        await s.execute(text("""
            UPDATE scribe_encounters SET status='approved',updated_at=NOW()
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id
        """),{"id":row["encounter_id"]})
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="scribe.note_approved",resource_type="scribe_note",resource_id=note_id,
                           outcome="approved",request_id=getattr(request.state,"request_id",None))
        return dict(row)

@router.post("/notes/{note_id}/commit")
async def commit_note(note_id:str,request:Request,tenant:TenantContext=Depends(require_permission("clinical_documentation:approve"))):
    if "approvals:approve" not in tenant.permissions: raise HTTPException(403,"note commit requires approval permission")
    async with tenant_session_context(tenant.organization_id) as s:
        note=(await s.execute(text("""
            SELECT n.id,n.encounter_id,n.note_text,e.patient_id
            FROM scribe_notes n JOIN scribe_encounters e ON e.id=n.encounter_id AND e.clinic_id=n.clinic_id
            WHERE n.clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND n.id=:id AND n.status='approved'
        """),{"id":note_id})).mappings().first()
        if not note: raise HTTPException(409,"only an approved note can be committed")
        record=(await s.execute(text("""
            INSERT INTO records_v2(clinic_id,patient_id,document_type,source,received_at,status,required,related_workflow_id)
            SELECT c.id,:patient_id,'clinical_note','hezqara_scribe',NOW(),'indexed',false,:encounter_id
            FROM clinics c WHERE c.clerk_org_id=current_setting('app.clerk_org_id',true)
            RETURNING id
        """),{"patient_id":note["patient_id"],"encounter_id":note["encounter_id"]})).mappings().one()
        updated=(await s.execute(text("""
            UPDATE scribe_notes SET status='committed',committed_at=NOW(),updated_at=NOW()
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id
            RETURNING id,status,committed_at
        """),{"id":note_id})).mappings().one()
        await s.execute(text("""
            UPDATE scribe_encounters SET status='committed',updated_at=NOW()
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id
        """),{"id":note["encounter_id"]})
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="scribe.note_committed",resource_type="scribe_note",resource_id=note_id,
                           outcome="committed",request_id=getattr(request.state,"request_id",None),
                           metadata={"record_id":record["id"]})
        return dict(updated)|{"record_id":record["id"]}
