from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.scheduling.schemas import AppointmentCreate

class SchedulingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    async def list(self, limit: int, offset: int):
        result = await self.session.execute(text("""select a.id,a.patient_id,a.appointment_datetime,a.duration_minutes,a.reason,a.appointment_type,a.status,a.created_at,a.updated_at
          from appointments a where a.clinic_id in (select c.id from clinics c where c.clerk_org_id=current_setting('app.clerk_org_id',true))
          order by a.appointment_datetime asc,a.id asc limit :limit offset :offset"""), {"limit": limit, "offset": offset})
        return [dict(r._mapping) for r in result]
    async def get(self, appointment_id: str):
        result = await self.session.execute(text("select id,patient_id,appointment_datetime,duration_minutes,reason,appointment_type,status,created_at,updated_at from appointments where id=:id"), {"id": appointment_id})
        row = result.mappings().first()
        return dict(row) if row else None
    async def create(self, data: AppointmentCreate):
        result = await self.session.execute(text("""insert into appointments (clinic_id,patient_id,appointment_datetime,duration_minutes,reason,appointment_type,status)
          select c.id,:patient_id,:appointment_datetime,:duration_minutes,:reason,:appointment_type,'scheduled' from clinics c
          where c.clerk_org_id=current_setting('app.clerk_org_id',true)
            and exists(select 1 from patients p where p.id=:patient_id and p.clinic_id=c.id)
          returning id,patient_id,appointment_datetime,duration_minutes,reason,appointment_type,status,created_at,updated_at"""), data.model_dump())
        row = result.mappings().first()
        if not row:
            raise ValueError("patient or organization not found")
        return dict(row)
