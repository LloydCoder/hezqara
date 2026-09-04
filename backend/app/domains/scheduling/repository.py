from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.scheduling.schemas import AppointmentCreate
class SchedulingRepository:
    def __init__(self, session: AsyncSession): self.session=session
    async def list(self, limit:int, offset:int):
        result=await self.session.execute(text("""select a.id,a.patient_id,a.starts_at,a.ends_at,a.appointment_type,a.status from appointments a join clinics c on c.id=a.clinic_id where c.clerk_org_id=current_setting('app.clerk_org_id', true) order by a.starts_at desc limit :limit offset :offset"""), {"limit":limit,"offset":offset})
        return [dict(r._mapping) for r in result]
    async def create(self,data:AppointmentCreate):
        result=await self.session.execute(text("""insert into appointments (clinic_id,patient_id,starts_at,ends_at,appointment_type,status) select c.id,:patient_id,:starts_at,:ends_at,:type,'scheduled' from clinics c where c.clerk_org_id=current_setting('app.clerk_org_id', true) and exists(select 1 from patients p where p.id=:patient_id and p.clinic_id=c.id) returning id,patient_id,starts_at,ends_at,appointment_type,status"""), {"patient_id":data.patient_id,"starts_at":data.starts_at,"ends_at":data.ends_at,"type":data.appointment_type})
        row=result.mappings().first()
        if not row: raise ValueError("patient or organization not found")
        return dict(row)
