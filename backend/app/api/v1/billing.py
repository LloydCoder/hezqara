from datetime import date
from decimal import Decimal
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel,Field
from sqlalchemy import text
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext

router=APIRouter(prefix='/billing',tags=['billing'])
class AccountCreate(BaseModel): patient_id:str; currency:str=Field(default='USD',pattern=r'^[A-Z]{3}$')
class ChargeCreate(BaseModel): patient_id:str; service_date:date; description:str=Field(min_length=1,max_length=500); amount:Decimal=Field(ge=0); payer_responsibility:Decimal=Field(default=0,ge=0); patient_responsibility:Decimal=Field(default=0,ge=0)
class PaymentCreate(BaseModel): account_id:str; amount:Decimal=Field(gt=0); status:str='pending'; idempotency_key:str=Field(min_length=8,max_length=200); provider:str|None=None

@router.post('/accounts',status_code=201)
async def create_account(data:AccountCreate,tenant:TenantContext=Depends(require_permission('billing:write'))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("insert into billing_accounts(clinic_id,patient_id,currency) select c.id,:patient,:currency from clinics c where c.clerk_org_id=current_setting('app.clerk_org_id',true) and exists(select 1 from patients p where p.id=:patient and p.clinic_id=c.id) on conflict(clinic_id,patient_id) do update set updated_at=now() returning id,patient_id,status,currency,created_at,updated_at"),data.model_dump())).mappings().first()
        if not row:raise HTTPException(404,'patient not found')
        return dict(row)

@router.get('/accounts')
async def list_accounts(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission('billing:read'))):
    async with tenant_session_context(tenant.organization_id) as s:
        rows=await s.execute(text("select a.id,a.patient_id,a.status,a.currency,a.created_at,a.updated_at,coalesce(sum(case when c.status<>'voided' then c.amount else 0 end),0) total_charges,coalesce(sum(case when c.status<>'voided' then c.patient_responsibility else 0 end),0) patient_responsibility from billing_accounts a left join billing_charges c on c.account_id=a.id where a.clinic_id in(select id from clinics where clerk_org_id=current_setting('app.clerk_org_id',true)) group by a.id order by a.updated_at desc limit :limit offset :offset"),{'limit':limit,'offset':offset});return [dict(r) for r in rows.mappings()]

@router.post('/charges',status_code=201)
async def create_charge(data:ChargeCreate,tenant:TenantContext=Depends(require_permission('billing:write'))):
    if data.payer_responsibility+data.patient_responsibility>data.amount:raise HTTPException(422,'responsibility cannot exceed charge amount')
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("insert into billing_charges(clinic_id,account_id,patient_id,service_date,description,amount,payer_responsibility,patient_responsibility) select a.clinic_id,a.id,a.patient_id,:date,:description,:amount,:payer,:patient from billing_accounts a where a.patient_id=:patient and a.clinic_id in(select id from clinics where clerk_org_id=current_setting('app.clerk_org_id',true)) returning id,account_id,patient_id,service_date,description,amount,payer_responsibility,patient_responsibility,status,created_at"),data.model_dump())).mappings().first()
        if not row:raise HTTPException(404,'billing account not found')
        return dict(row)

@router.post('/payments',status_code=201)
async def create_payment(data:PaymentCreate,tenant:TenantContext=Depends(require_permission('billing:write'))):
    allowed={'pending','authorized','paid','failed','refunded','voided'}
    if data.status not in allowed:raise HTTPException(422,'invalid payment state')
    async with tenant_session_context(tenant.organization_id) as s:
        row=(await s.execute(text("insert into billing_payments(clinic_id,account_id,amount,status,provider,idempotency_key) select a.clinic_id,a.id,:amount,:status,:provider,:key from billing_accounts a where a.id=:account and a.clinic_id in(select id from clinics where clerk_org_id=current_setting('app.clerk_org_id',true)) on conflict(clinic_id,idempotency_key) do update set id=billing_payments.id returning id,account_id,amount,status,provider,provider_reference,created_at,updated_at"),{'amount':data.amount,'status':data.status,'provider':data.provider,'key':data.idempotency_key,'account':data.account_id})).mappings().first()
        if not row:raise HTTPException(404,'billing account not found')
        return dict(row)
