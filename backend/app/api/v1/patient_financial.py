from datetime import date
from decimal import Decimal
import json
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event

router=APIRouter(prefix="/patient-financial",tags=["patient-financial"])

class StatementCreate(BaseModel):
    account_id:str
    amount_due:Decimal=Field(ge=0)
    due_date:date|None=None
    delivery_channel:str="portal"

class CostEstimateCreate(BaseModel):
    patient_id:str
    account_id:str|None=None
    coverage_id:str|None=None
    services:list[dict]=Field(min_length=1)
    estimated_charges:Decimal=Field(ge=0)
    estimated_payer_responsibility:Decimal=Field(default=0,ge=0)
    estimated_patient_responsibility:Decimal=Field(default=0,ge=0)
    assumptions:list[str]=Field(default_factory=list)
    expires_at:str|None=None

class PaymentPlanCreate(BaseModel):
    account_id:str
    total_amount:Decimal=Field(gt=0)
    installment_amount:Decimal=Field(gt=0)
    frequency:str
    next_due_date:date|None=None

class AssistanceCreate(BaseModel):
    account_id:str
    requested_amount:Decimal=Field(ge=0)
    reason:str|None=None
    evidence:list[dict]=Field(default_factory=list)

class AssistanceDecision(BaseModel):
    status:str
    approved_amount:Decimal|None=Field(default=None,ge=0)

class ReconcilePayment(BaseModel):
    payment_id:str
    account_id:str
    applied_amount:Decimal=Field(gt=0)
    external_reference:str|None=None
    notes:str|None=None

def _validate_channel(channel):
    if channel not in {"portal","email","sms","mail","staff"}: raise HTTPException(422,"invalid delivery channel")

@router.post("/statements",status_code=201)
async def create_statement(data:StatementCreate,request:Request,tenant:TenantContext=Depends(require_permission("billing:write"))):
    _validate_channel(data.delivery_channel)
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            INSERT INTO patient_statements
              (clinic_id,account_id,patient_id,statement_number,amount_due,due_date,status,delivery_channel,issued_at)
            SELECT a.clinic_id,a.id,a.patient_id,
                   'HZ-' || to_char(NOW(),'YYYYMMDDHH24MISSMS') || '-' || substr(a.id,1,8),
                   :amount_due,:due_date,'issued',:delivery_channel,NOW()
            FROM billing_accounts a
            WHERE a.id=:account_id
              AND a.clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
            RETURNING id,account_id,patient_id,statement_number,amount_due,due_date,status,delivery_channel,issued_at,created_at,updated_at
        """),data.model_dump())).mappings().first()
        if not row: raise HTTPException(404,"billing account not found")
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="patient_financial.statement_issued",resource_type="patient_statement",
                           resource_id=row["id"],outcome="issued",request_id=getattr(request.state,"request_id",None))
        return dict(row)

@router.get("/statements")
async def list_statements(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission("billing:read"))):
    async with tenant_session_context(tenant.organization_id) as s:
        rows=await s.execute(text("""
            SELECT id,account_id,patient_id,statement_number,amount_due,due_date,status,delivery_channel,
                   issued_at,created_at,updated_at
            FROM patient_statements
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
            ORDER BY created_at DESC LIMIT :limit OFFSET :offset
        """),{"limit":limit,"offset":offset})
        return [dict(r) for r in rows.mappings()]

@router.post("/estimates",status_code=201)
async def create_estimate(data:CostEstimateCreate,request:Request,tenant:TenantContext=Depends(require_permission("billing:write"))):
    if data.estimated_payer_responsibility+data.estimated_patient_responsibility>data.estimated_charges:
        raise HTTPException(422,"estimated responsibilities cannot exceed estimated charges")
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            INSERT INTO cost_estimates
              (clinic_id,patient_id,account_id,coverage_id,services,estimated_charges,
               estimated_payer_responsibility,estimated_patient_responsibility,assumptions,expires_at,created_by)
            SELECT c.id,:patient_id,:account_id,:coverage_id,:services::jsonb,:estimated_charges,
                   :estimated_payer_responsibility,:estimated_patient_responsibility,:assumptions::jsonb,
                   :expires_at,:created_by
            FROM clinics c
            WHERE c.clerk_org_id=current_setting('app.clerk_org_id',true)
              AND EXISTS (SELECT 1 FROM patients p WHERE p.id=:patient_id AND p.clinic_id=c.id)
              AND (:account_id IS NULL OR EXISTS (SELECT 1 FROM billing_accounts a WHERE a.id=:account_id AND a.clinic_id=c.id AND a.patient_id=:patient_id))
            RETURNING *
        """),{**data.model_dump(),"services":json.dumps(data.services),"assumptions":json.dumps(data.assumptions),
              "created_by":tenant.user_id})).mappings().first()
        if not row: raise HTTPException(404,"patient or account not found")
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="patient_financial.estimate_created",resource_type="cost_estimate",
                           resource_id=row["id"],outcome="estimate",request_id=getattr(request.state,"request_id",None))
        return dict(row)|{"disclaimer":"Estimate only; final patient responsibility may differ after payer adjudication."}

@router.post("/payment-plans",status_code=201)
async def create_payment_plan(data:PaymentPlanCreate,request:Request,tenant:TenantContext=Depends(require_permission("billing:write"))):
    if data.frequency not in {"weekly","biweekly","monthly"}: raise HTTPException(422,"invalid payment-plan frequency")
    if data.installment_amount>data.total_amount: raise HTTPException(422,"installment cannot exceed total")
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            INSERT INTO payment_plans(clinic_id,account_id,patient_id,total_amount,remaining_amount,installment_amount,frequency,next_due_date,created_by)
            SELECT a.clinic_id,a.id,a.patient_id,:total_amount,:total_amount,:installment_amount,:frequency,:next_due_date,:created_by
            FROM billing_accounts a
            WHERE a.id=:account_id AND a.clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
            RETURNING id,account_id,patient_id,total_amount,remaining_amount,installment_amount,frequency,next_due_date,status,created_at,updated_at
        """),{**data.model_dump(),"created_by":tenant.user_id})).mappings().first()
        if not row: raise HTTPException(404,"billing account not found")
        return dict(row)

@router.get("/payment-plans")
async def list_payment_plans(account_id:str|None=None,tenant:TenantContext=Depends(require_permission("billing:read"))):
    async with tenant_session_context(tenant.organization_id) as s:
        rows=await s.execute(text("""
            SELECT id,account_id,patient_id,total_amount,remaining_amount,installment_amount,frequency,next_due_date,status,created_at,updated_at
            FROM payment_plans
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND (:account_id IS NULL OR account_id=:account_id)
            ORDER BY created_at DESC
        """),{"account_id":account_id})
        return [dict(r) for r in rows.mappings()]

@router.post("/assistance",status_code=201)
async def request_assistance(data:AssistanceCreate,request:Request,tenant:TenantContext=Depends(require_permission("billing:write"))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            INSERT INTO financial_assistance_cases(clinic_id,account_id,patient_id,requested_amount,reason,evidence)
            SELECT a.clinic_id,a.id,a.patient_id,:requested_amount,:reason,:evidence::jsonb
            FROM billing_accounts a
            WHERE a.id=:account_id AND a.clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
            RETURNING *
        """),{**data.model_dump(),"evidence":json.dumps(data.evidence)})).mappings().first()
        if not row: raise HTTPException(404,"billing account not found")
        return dict(row)

@router.post("/assistance/{case_id}/decision")
async def decide_assistance(case_id:str,data:AssistanceDecision,request:Request,tenant:TenantContext=Depends(require_permission("billing:write"))):
    if data.status not in {"approved","denied","cancelled"}: raise HTTPException(422,"invalid assistance decision")
    if data.status=="approved" and data.approved_amount is None: raise HTTPException(422,"approved_amount is required")
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            UPDATE financial_assistance_cases
            SET status=:status,approved_amount=:approved_amount,reviewer_id=:reviewer_id,
                reviewed_at=NOW(),updated_at=NOW()
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND id=:id
            RETURNING *
        """),{"id":case_id,"status":data.status,"approved_amount":data.approved_amount,"reviewer_id":tenant.user_id})).mappings().first()
        if not row: raise HTTPException(404,"assistance case not found")
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,
                           action="patient_financial.assistance_decided",resource_type="financial_assistance_case",
                           resource_id=case_id,outcome=data.status,request_id=getattr(request.state,"request_id",None))
        return dict(row)

@router.post("/reconcile",status_code=201)
async def reconcile_payment(data:ReconcilePayment,request:Request,tenant:TenantContext=Depends(require_permission("billing:write"))):
    async with tenant_session_context(tenant.organization_id) as s:
        payment=(await s.execute(text("""
            SELECT id,account_id,amount,status FROM billing_payments
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND id=:id FOR UPDATE
        """),{"id":data.payment_id})).mappings().first()
        if not payment: raise HTTPException(404,"payment not found")
        if data.account_id!=payment["account_id"]: raise HTTPException(409,"payment/account mismatch")
        existing=(await s.execute(text("""
            SELECT COALESCE(SUM(applied_amount),0) FROM payment_reconciliations
            WHERE clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
              AND payment_id=:payment_id AND status='reconciled'
        """),{"payment_id":data.payment_id})).scalar_one()
        if Decimal(str(existing))+data.applied_amount>Decimal(str(payment["amount"])):
            raise HTTPException(409,"reconciliation exceeds payment amount")
        row=(await s.execute(text("""
            INSERT INTO payment_reconciliations(clinic_id,payment_id,account_id,applied_amount,external_reference,notes)
            VALUES ((SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)),:payment_id,:account_id,:applied_amount,:external_reference,:notes)
            RETURNING id,payment_id,account_id,applied_amount,external_reference,status,created_at
        """),data.model_dump())).mappings().one()
        return dict(row)

@router.get("/summary/{account_id}")
async def financial_summary(account_id:str,tenant:TenantContext=Depends(require_permission("billing:read"))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("""
            SELECT a.id,a.patient_id,a.currency,
              COALESCE((SELECT SUM(amount) FROM billing_charges c WHERE c.account_id=a.id AND c.status<>'voided'),0) charges,
              COALESCE((SELECT SUM(amount) FROM billing_payments p WHERE p.account_id=a.id AND p.status='paid'),0) payments,
              COALESCE((SELECT SUM(applied_amount) FROM payment_reconciliations r WHERE r.account_id=a.id AND r.status='reconciled'),0) reconciled,
              COALESCE((SELECT SUM(remaining_amount) FROM payment_plans pp WHERE pp.account_id=a.id AND pp.status='active'),0) plan_remaining
            FROM billing_accounts a
            WHERE a.id=:id AND a.clinic_id=(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))
        """),{"id":account_id})).mappings().first()
        if not row: raise HTTPException(404,"billing account not found")
        return dict(row)
