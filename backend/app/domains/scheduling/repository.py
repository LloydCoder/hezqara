from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.scheduling.schemas import AppointmentCreate,AppointmentUpdate
class SchedulingRepository:
    def __init__(self,session:AsyncSession):self.session=session
    async def list(self,limit:int,offset:int):
        result=await self.session.execute(text("""select a.id,a.patient_id,trim(p.first_name||' '||p.last_name) as patient_name,a.appointment_datetime,a.duration_minutes,a.reason,a.status,a.created_at,a.updated_at
          from appointments a join patients p on p.id=a.patient_id where a.clinic_id in (select c.id from clinics c where c.clerk_org_id=current_setting('app.clerk_org_id',true)) order by a.appointment_datetime asc,a.id asc limit :limit offset :offset"""),{'limit':limit,'offset':offset});return [dict(r._mapping) for r in result]
    async def get(self,appointment_id:str):
        result=await self.session.execute(text("""select a.id,a.patient_id,trim(p.first_name||' '||p.last_name) as patient_name,a.appointment_datetime,a.duration_minutes,a.reason,a.status,a.created_at,a.updated_at from appointments a join patients p on p.id=a.patient_id where a.id=:id"""),{'id':appointment_id});row=result.mappings().first();return dict(row) if row else None
    async def create(self,data:AppointmentCreate):
        result=await self.session.execute(text("""insert into appointments (clinic_id,patient_id,appointment_datetime,duration_minutes,reason,status)
          select c.id,:patient_id,:appointment_datetime,:duration_minutes,:reason,'scheduled' from clinics c
          where c.clerk_org_id=current_setting('app.clerk_org_id',true) and exists(select 1 from patients p where p.id=:patient_id and p.clinic_id=c.id)
          returning id"""),{'patient_id':data.patient_id,'appointment_datetime':data.appointment_datetime,'duration_minutes':data.duration_minutes,'reason':data.reason})
        row=result.mappings().first()
        if not row:raise ValueError('patient or organization not found')
        return await self.get(row['id'])
    async def update(self,appointment_id:str,data:AppointmentUpdate):
        values=data.model_dump(exclude_unset=True)
        if not values:return await self.get(appointment_id)
        result=await self.session.execute(text("update appointments set status=coalesce(:status,status),reason=coalesce(:reason,reason),updated_at=now() where id=:id returning id"),{'id':appointment_id,'status':values.get('status'),'reason':values.get('reason')});row=result.mappings().first();return await self.get(row['id']) if row else None
