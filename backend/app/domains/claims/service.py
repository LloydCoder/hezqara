from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.claims.engine import validate_claim_transition

class ClaimsService:
    def __init__(self,session:AsyncSession): self.session=session
    async def list(self,limit:int,offset:int):
        rows=await self.session.execute(text('select id,patient_id,payer_name,billed_amount,expected_amount,paid_amount,patient_responsibility,status,payer_reference,submitted_at,responded_at,created_at,updated_at from claims order by updated_at desc,id desc limit :limit offset :offset'),{'limit':limit,'offset':offset}); return [dict(r) for r in rows.mappings()]
    async def create(self,patient_id:str,payer_name:str,billed_amount,expected_amount=None,coverage_id=None):
        row=(await self.session.execute(text("insert into claims(clinic_id,patient_id,coverage_id,payer_name,billed_amount,expected_amount) select c.id,:patient,:coverage,:payer,:amount,:expected from clinics c where c.clerk_org_id=current_setting('app.clerk_org_id',true) and exists(select 1 from patients p where p.id=:patient and p.clinic_id=c.id) and (:coverage is null or exists(select 1 from patient_coverages pc where pc.id=:coverage and pc.clinic_id=c.id and pc.patient_id=:patient)) returning id,patient_id,payer_name,billed_amount,expected_amount,paid_amount,patient_responsibility,status,created_at,updated_at"),{'patient':patient_id,'coverage':coverage_id,'payer':payer_name,'amount':billed_amount,'expected':expected_amount})).mappings().first()
        if not row: raise ValueError('patient or coverage not found')
        return dict(row)
    async def transition(self,claim_id:str,target:str):
        row=(await self.session.execute(text('select id,status from claims where id=:id for update'),{'id':claim_id})).mappings().first()
        if not row:return None
        validate_claim_transition(row['status'],target)
        updated=(await self.session.execute(text("update claims set status=:status,submitted_at=case when :status='submitted' then coalesce(submitted_at,now()) else submitted_at end,updated_at=now() where id=:id returning id,status,submitted_at,updated_at"),{'id':claim_id,'status':target})).mappings().first(); return dict(updated)
