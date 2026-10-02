from decimal import Decimal
import json
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event
from app.domains.claims.engine import validate_claim_transition, aging_bucket

router=APIRouter(prefix="/revenue-cycle",tags=["revenue-cycle"])

class ClaimLineCreate(BaseModel):
    service_date:str
    service_code:str=Field(min_length=1,max_length=50)
    description:str|None=None
    amount:Decimal=Field(gt=0)
    units:Decimal=Field(default=Decimal("1"),gt=0)

class ClaimCreateV2(BaseModel):
    patient_id:str
    payer_name:str=Field(min_length=1,max_length=200)
    billed_amount:Decimal=Field(ge=0)
    expected_amount:Decimal|None=Field(default=None,ge=0)
    coverage_id:str|None=None
    idempotency_key:str=Field(min_length=8,max_length=200)
    lines:list[ClaimLineCreate]=Field(min_length=1)

class ClaimTransition(BaseModel):
    status:str
    reason:str|None=None

class ClaimSubmission(BaseModel):
    idempotency_key:str=Field(min_length=8,max_length=200)
    transport:str="adapter"

class AdjudicationCreate(BaseModel):
    payer_reference:str|None=None
    allowed_amount:Decimal|None=Field(default=None,ge=0)
    paid_amount:Decimal=Field(ge=0)
    deductible:Decimal=Field(default=Decimal("0"),ge=0)
    coinsurance:Decimal=Field(default=Decimal("0"),ge=0)
    copay:Decimal=Field(default=Decimal("0"),ge=0)
    patient_responsibility:Decimal=Field(default=Decimal("0"),ge=0)
    adjustment_reason:str|None=None

class DenialCreate(BaseModel):
    denial_code:str|None=None
    category:str="unknown"
    amount:Decimal=Field(ge=0)
    deadline_at:str|None=None
    recommended_action:str|None=None

class AppealCreate(BaseModel):
    argument:str|None=None
    evidence:list[dict]=Field(default_factory=list)

class ARUpdate(BaseModel):
    status:str
    owner_id:str|None=None
    next_follow_up_at:str|None=None
    notes:str|None=None

async def _clinic_id(session):
    row=(await session.execute(text("SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)"))).first()
    if not row: raise HTTPException(404,"clinic not found")
    return row[0]

@router.post("/claims",status_code=201)
async def create_claim(data:ClaimCreateV2,request:Request,tenant:TenantContext=Depends(require_permission("claims:write"))):
    async with tenant_session_context(tenant.organization_id) as s:
        existing=(await s.execute(text("""
            SELECT id,patient_id,payer_name,billed_amount,expected_amount,paid_amount,patient_responsibility,status,
                   payer_reference,submitted_at,responded_at,created_at,updated_at
            FROM claims WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND creation_idempotency_key=:key
        """),{"key":data.idempotency_key})).mappings().first()
        if existing: return dict(existing)
        row=(await s.execute(text("""
            INSERT INTO claims(clinic_id,patient_id,coverage_id,payer_name,billed_amount,expected_amount,creation_idempotency_key)
            SELECT c.id,:patient_id,:coverage_id,:payer_name,:billed_amount,:expected_amount,:idempotency_key
            FROM clinics c
            WHERE c.clerk_org_id=current_setting('app.clerk_org_id',true)
              AND EXISTS (SELECT 1 FROM patients p WHERE p.id=:patient_id AND p.clinic_id=c.id)
              AND (:coverage_id IS NULL OR EXISTS
                   (SELECT 1 FROM patient_coverages pc WHERE pc.id=:coverage_id AND pc.clinic_id=c.id AND pc.patient_id=:patient_id))
            RETURNING id,patient_id,payer_name,billed_amount,expected_amount,paid_amount,patient_responsibility,status,
                      payer_reference,submitted_at,responded_at,created_at,updated_at
        """),data.model_dump(exclude={"lines"}))).mappings().first()
        if not row: raise HTTPException(404,"patient or coverage not found")
        for line in data.lines:
            await s.execute(text("""
                INSERT INTO claim_lines(clinic_id,claim_id,service_date,service_code,description,amount,units)
                SELECT clinic_id,:claim_id,:service_date,:service_code,:description,:amount,:units
                FROM claims WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
                  AND id=:claim_id
            """),line.model_dump()|{"claim_id":row["id"]})
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="claim.created",resource_type="claim",resource_id=row["id"],
                           outcome="draft",request_id=getattr(request.state,"request_id",None))
        return dict(row)

@router.post("/claims/{claim_id}/scrub")
async def scrub_claim(claim_id:str,request:Request,tenant:TenantContext=Depends(require_permission("claims:write"))):
    async with tenant_session_context(tenant.organization_id) as s:
        claim=(await s.execute(text("""
            SELECT id,patient_id,coverage_id,payer_name,billed_amount,expected_amount,status
            FROM claims WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND id=:id
        """),{"id":claim_id})).mappings().first()
        if not claim: raise HTTPException(404,"claim not found")
        lines=(await s.execute(text("""
            SELECT service_code,amount,units FROM claim_lines
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND claim_id=:id ORDER BY id
        """),{"id":claim_id})).mappings().all()
        issues=[]
        if not lines: issues.append({"code":"NO_LINES","message":"claim has no claim lines"})
        if claim["billed_amount"] < 0: issues.append({"code":"NEGATIVE_BILLED","message":"billed amount cannot be negative"})
        line_total=sum((Decimal(str(x["amount"]))*Decimal(str(x["units"])) for x in lines),Decimal("0"))
        if lines and abs(line_total-Decimal(str(claim["billed_amount"]))) > Decimal("0.01"):
            issues.append({"code":"LINE_TOTAL_MISMATCH","message":"claim line total does not reconcile to billed amount"})
        if claim["coverage_id"] is None: issues.append({"code":"MISSING_COVERAGE","message":"coverage is required for payer claim submission"})
        for line in lines:
            if not line["service_code"].strip(): issues.append({"code":"MISSING_SERVICE_CODE","message":"claim line is missing service code"})
            if Decimal(str(line["amount"])) <= 0: issues.append({"code":"INVALID_LINE_AMOUNT","message":"claim line amount must be positive"})
        status="failed" if issues else "passed"
        row=(await s.execute(text("""
            INSERT INTO claim_scrub_results(clinic_id,claim_id,status,issues)
            VALUES ((SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)),:claim_id,:status,:issues::jsonb)
            RETURNING id,claim_id,status,issues,ruleset_version,created_at
        """),{"claim_id":claim_id,"status":status,"issues":json.dumps(issues)})).mappings().one()
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="claim.scrubbed",resource_type="claim",resource_id=claim_id,
                           outcome=status,request_id=getattr(request.state,"request_id",None),
                           metadata={"issue_count":len(issues)})
        return dict(row)

@router.get("/claims/{claim_id}/scrub")
async def get_latest_scrub(claim_id:str,tenant:TenantContext=Depends(require_permission("claims:read"))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            SELECT id,claim_id,status,issues,ruleset_version,created_at
            FROM claim_scrub_results
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND claim_id=:id ORDER BY created_at DESC LIMIT 1
        """),{"id":claim_id})).mappings().first()
        if not row: raise HTTPException(404,"no scrub result")
        return dict(row)

@router.post("/claims/{claim_id}/transition")
async def transition_claim(claim_id:str,data:ClaimTransition,request:Request,tenant:TenantContext=Depends(require_permission("claims:write"))):
    if data.status=="submitted" and "approvals:approve" not in tenant.permissions:
        raise HTTPException(403,"claim submission requires approval permission")
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            SELECT id,status FROM claims
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND id=:id FOR UPDATE
        """),{"id":claim_id})).mappings().first()
        if not row: raise HTTPException(404,"claim not found")
        if data.status=="ready":
            scrub=(await s.execute(text("""
                SELECT status FROM claim_scrub_results
                WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
                  AND claim_id=:id ORDER BY created_at DESC LIMIT 1
            """),{"id":claim_id})).scalar_one_or_none()
            if scrub!="passed": raise HTTPException(409,"claim must pass the latest scrub before becoming ready")
        try: validate_claim_transition(row["status"],data.status)
        except ValueError as exc: raise HTTPException(409,str(exc)) from exc
        updated=(await s.execute(text("""
            UPDATE claims SET status=:status,
              submitted_at=CASE WHEN :status='submitted' THEN COALESCE(submitted_at,NOW()) ELSE submitted_at END,
              updated_at=NOW()
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND id=:id
            RETURNING id,status,submitted_at,updated_at
        """),{"id":claim_id,"status":data.status})).mappings().one()
        await s.execute(text("""
            INSERT INTO claim_events(clinic_id,claim_id,from_status,to_status,actor,reason)
            SELECT clinic_id,id,:from_status,:to_status,:actor,:reason FROM claims WHERE id=:id
        """),{"id":claim_id,"from_status":row["status"],"to_status":data.status,"actor":tenant.user_id,"reason":data.reason})
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="claim.status_changed",resource_type="claim",resource_id=claim_id,
                           outcome=data.status,request_id=getattr(request.state,"request_id",None))
        return dict(updated)

@router.post("/claims/{claim_id}/submit")
async def submit_claim(claim_id:str,data:ClaimSubmission,request:Request,tenant:TenantContext=Depends(require_permission("claims:submit"))):
    if "approvals:approve" not in tenant.permissions: raise HTTPException(403,"claim submission requires approval permission")
    async with tenant_session_context(tenant.organization_id) as s:
        scrub=(await s.execute(text("""
            SELECT status FROM claim_scrub_results WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
            AND claim_id=:id ORDER BY created_at DESC LIMIT 1
        """),{"id":claim_id})).scalar_one_or_none()
        if scrub!="passed": raise HTTPException(409,"claim must pass scrub before submission")
        claim=(await s.execute(text("""
            SELECT id,status FROM claims WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id FOR UPDATE
        """),{"id":claim_id})).mappings().first()
        if not claim: raise HTTPException(404,"claim not found")
        if claim["status"]!="ready": raise HTTPException(409,"claim must be ready before submission")
        attempt=(await s.execute(text("""
            INSERT INTO claim_submission_attempts(clinic_id,claim_id,idempotency_key,transport,status)
            VALUES ((SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)),:claim_id,:key,:transport,'submitted')
            ON CONFLICT (clinic_id,idempotency_key) DO UPDATE SET updated_at=claim_submission_attempts.updated_at
            RETURNING id,claim_id,idempotency_key,transport,status,external_reference,error,created_at,updated_at
        """),{"claim_id":claim_id,"key":data.idempotency_key,"transport":data.transport})).mappings().one()
        await s.execute(text("""
            UPDATE claims SET status='submitted',submitted_at=COALESCE(submitted_at,NOW()),updated_at=NOW()
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id
        """),{"id":claim_id})
        return dict(attempt)

@router.post("/claims/{claim_id}/adjudication")
async def record_adjudication(claim_id:str,data:AdjudicationCreate,request:Request,tenant:TenantContext=Depends(require_permission("claims:write"))):
    async with tenant_session_context(tenant.organization_id) as s:
        claim=(await s.execute(text("""
            SELECT id,patient_id,payer_name,billed_amount,status FROM claims
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id FOR UPDATE
        """),{"id":claim_id})).mappings().first()
        if not claim: raise HTTPException(404,"claim not found")
        status="paid" if data.paid_amount >= Decimal(str(claim["billed_amount"])) else "partially_paid"
        if data.paid_amount==0: status="denied"
        adj=(await s.execute(text("""
            INSERT INTO claim_adjudications(clinic_id,claim_id,payer_reference,billed_amount,allowed_amount,paid_amount,
              deductible,coinsurance,copay,patient_responsibility,adjustment_reason)
            VALUES ((SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)),:claim_id,:payer_reference,
              :billed_amount,:allowed_amount,:paid_amount,:deductible,:coinsurance,:copay,:patient_responsibility,:adjustment_reason)
            RETURNING id,claim_id,payer_reference,billed_amount,allowed_amount,paid_amount,patient_responsibility,received_at
        """),{"claim_id":claim_id,"payer_reference":data.payer_reference,"billed_amount":claim["billed_amount"],
               **data.model_dump(exclude={"payer_reference"})})).mappings().one()
        await s.execute(text("""
            UPDATE claims SET paid_amount=:paid_amount,patient_responsibility=:patient_responsibility,
              status=:status,responded_at=NOW(),updated_at=NOW()
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id
        """),{"claim_id":claim_id,"id":claim_id,"paid_amount":data.paid_amount,"patient_responsibility":data.patient_responsibility,"status":status})
        outstanding=max(Decimal("0"),Decimal(str(claim["billed_amount"]))-data.paid_amount)
        if outstanding>0:
            await s.execute(text("""
                INSERT INTO ar_work_items(clinic_id,claim_id,patient_id,responsibility,amount,aging_bucket,status,notes)
                VALUES ((SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)),:claim_id,:patient_id,
                        'payer',:amount,'0_30','open','Created from adjudication')
            """),{"claim_id":claim_id,"patient_id":claim["patient_id"],"amount":outstanding})
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="claim.adjudicated",resource_type="claim",resource_id=claim_id,
                           outcome=status,request_id=getattr(request.state,"request_id",None))
        return dict(adj)|{"claim_status":status}

@router.get("/ar")
async def list_ar(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission("claims:read"))):
    async with tenant_session_context(tenant.organization_id) as s:
        rows=await s.execute(text("""
            SELECT id,claim_id,patient_id,responsibility,amount,aging_bucket,status,owner_id,next_follow_up_at,notes,created_at,updated_at
            FROM ar_work_items WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
            ORDER BY updated_at DESC,id DESC LIMIT :limit OFFSET :offset
        """),{"limit":limit,"offset":offset})
        return [dict(r) for r in rows.mappings()]

@router.patch("/ar/{item_id}")
async def update_ar(item_id:str,data:ARUpdate,request:Request,tenant:TenantContext=Depends(require_permission("claims:write"))):
    if data.status not in {"open","assigned","follow_up","escalated","resolved","closed"}:
        raise HTTPException(422,"invalid A/R status")
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            UPDATE ar_work_items SET status=:status,owner_id=COALESCE(:owner_id,owner_id),
              next_follow_up_at=:next_follow_up_at,notes=COALESCE(:notes,notes),updated_at=NOW()
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id
            RETURNING id,claim_id,status,owner_id,next_follow_up_at,notes,updated_at
        """),{"id":item_id,**data.model_dump()})).mappings().first()
        if not row: raise HTTPException(404,"A/R work item not found")
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="ar.updated",resource_type="ar_work_item",resource_id=item_id,
                           outcome=data.status,request_id=getattr(request.state,"request_id",None))
        return dict(row)

@router.get("/denials")
async def list_denials(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission("claims:read"))):
    async with tenant_session_context(tenant.organization_id) as s:
        rows=await s.execute(text("""
            SELECT id,claim_id,denial_code,category,payer_name,amount,received_at,deadline_at,status,
                   owner_id,recommended_action,appeal_state,created_at,updated_at
            FROM denials WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
            ORDER BY deadline_at NULLS LAST,created_at DESC LIMIT :limit OFFSET :offset
        """),{"limit":limit,"offset":offset})
        return [dict(r) for r in rows.mappings()]

@router.post("/claims/{claim_id}/denial",status_code=201)
async def create_denial(claim_id:str,data:DenialCreate,request:Request,tenant:TenantContext=Depends(require_permission("claims:write"))):
    async with tenant_session_context(tenant.organization_id) as s:
        claim=(await s.execute(text("""
            SELECT id,payer_name FROM claims WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id
        """),{"id":claim_id})).mappings().first()
        if not claim: raise HTTPException(404,"claim not found")
        denial=(await s.execute(text("""
            INSERT INTO denials(clinic_id,claim_id,denial_code,category,payer_name,amount,deadline_at,recommended_action)
            VALUES ((SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)),:claim_id,:denial_code,:category,:payer_name,:amount,:deadline_at,:recommended_action)
            RETURNING id,claim_id,denial_code,category,payer_name,amount,deadline_at,status,appeal_state,created_at,updated_at
        """),{"claim_id":claim_id,"payer_name":claim["payer_name"],**data.model_dump()})).mappings().one()
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="denial.created",resource_type="denial",resource_id=denial["id"],
                           outcome="open",request_id=getattr(request.state,"request_id",None))
        return dict(denial)

@router.post("/denials/{denial_id}/appeal",status_code=201)
async def create_appeal(denial_id:str,data:AppealCreate,request:Request,tenant:TenantContext=Depends(require_permission("claims:write"))):
    async with tenant_session_context(tenant.organization_id) as s:
        denial=(await s.execute(text("""
            SELECT id,status FROM denials WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id FOR UPDATE
        """),{"id":denial_id})).mappings().first()
        if not denial: raise HTTPException(404,"denial not found")
        appeal=(await s.execute(text("""
            INSERT INTO denial_appeals(clinic_id,denial_id,status,argument,evidence,created_by)
            VALUES ((SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)),:denial_id,'draft',:argument,:evidence::jsonb,:actor)
            RETURNING id,denial_id,status,argument,evidence,created_at,updated_at
        """),{"denial_id":denial_id,"argument":data.argument,"evidence":json.dumps(data.evidence),"actor":tenant.user_id})).mappings().one()
        await s.execute(text("UPDATE denials SET status='in_review',appeal_state='draft',updated_at=NOW() WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id"),{"id":denial_id})
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="denial.appeal_created",resource_type="denial_appeal",resource_id=appeal["id"],
                           outcome="draft",request_id=getattr(request.state,"request_id",None))
        return dict(appeal)

@router.post("/denials/{denial_id}/appeal/submit")
async def submit_appeal(denial_id:str,request:Request,tenant:TenantContext=Depends(require_permission("claims:submit"))):
    if "approvals:approve" not in tenant.permissions: raise HTTPException(403,"appeal submission requires approval permission")
    async with tenant_session_context(tenant.organization_id) as s:
        appeal=(await s.execute(text("""
            SELECT id,status FROM denial_appeals
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND denial_id=:denial_id
            ORDER BY created_at DESC LIMIT 1 FOR UPDATE
        """),{"denial_id":denial_id})).mappings().first()
        if not appeal: raise HTTPException(404,"appeal not found")
        if appeal["status"] not in ("draft","ready"): raise HTTPException(409,"appeal is not submit-ready")
        updated=(await s.execute(text("""
            UPDATE denial_appeals SET status='submitted',submitted_at=NOW(),updated_at=NOW()
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id
            RETURNING id,denial_id,status,submitted_at
        """),{"id":appeal["id"]})).mappings().one()
        await s.execute(text("UPDATE denials SET status='appealed',appeal_state='submitted',updated_at=NOW() WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) AND id=:id"),{"id":denial_id})
        return dict(updated)
