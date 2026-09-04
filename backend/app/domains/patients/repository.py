from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.patients.schemas import PatientCreate

class PatientRepository:
    def __init__(self, session: AsyncSession): self.session = session
    async def list(self, limit: int, offset: int):
        result = await self.session.execute(text("""select p.id,p.first_name,p.last_name,p.date_of_birth,p.phone,p.email,p.insurance_carrier,p.insurance_member_id,p.created_at,p.updated_at from patients p join clinics c on c.id=p.clinic_id where c.clerk_org_id=current_setting('app.clerk_org_id', true) order by p.created_at desc limit :limit offset :offset"""), {"limit":limit,"offset":offset})
        return [dict(r._mapping) for r in result]
    async def create(self, data: PatientCreate):
        result = await self.session.execute(text("""insert into patients (clinic_id,first_name,last_name,date_of_birth,phone,email,insurance_carrier,insurance_member_id) select c.id,:first_name,:last_name,:dob,:phone,:email,:carrier,:member from clinics c where c.clerk_org_id=current_setting('app.clerk_org_id', true) returning id,first_name,last_name,date_of_birth,phone,email,insurance_carrier,insurance_member_id,created_at,updated_at"""), {"first_name":data.first_name,"last_name":data.last_name,"dob":data.date_of_birth,"phone":data.phone,"email":data.email,"carrier":data.insurance_carrier,"member":data.insurance_member_id})
        row = result.mappings().first()
        if not row: raise ValueError("organization clinic is not provisioned")
        return dict(row)
