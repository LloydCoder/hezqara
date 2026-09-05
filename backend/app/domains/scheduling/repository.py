from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.scheduling.schemas import AppointmentCreate,AppointmentUpdate

class SchedulingRepository:
    def __init__(self,session:AsyncSession): self.session=session
    async def list(self,limit:int,offset:int):
        result=await self.session.execute(text("select a.id,a.patient_id,trim(p.first_name||' '||p.last_name) as patient_name,a.provider_id,a.provider_name,a.appointment_datetime,a.duration_minutes,a.reason,a.status,a.created_at,a.updated_at from appointments a join patients p on p.id=a.patient_id where a.clinic_id in (select c.id from clinics c where c.clerk_org_id=current_setting('app.clerk_org_id',true)) order by a.appointment_datetime asc,a.id asc limit :limit offset :offset"),{'limit':limit,'offset':offset}); return [dict(r._mapping) for r in result]
    async def get(self,appointment_id:str):
        result=await self.session.execute(text("select a.id,a.patient_id,trim(p.first_name||' '||p.last_name) as patient_name,a.provider_id,a.provider_name,a.appointment_datetime,a.duration_minutes,a.reason,a.status,a.created_at,a.updated_at from appointments a join patients p on p.id=a.patient_id where a.id=:id and a.clinic_id in (select c.id from clinics c where c.clerk_org_id=current_setting('app.clerk_org_id',true))"),{'id':appointment_id}); row=result.mappings().first(); return dict(row) if row else None
    async def availability(self,provider_id:str|None,start,end,duration_minutes:int,limit:int=20):
        result=await self.session.execute(text("select a.id,a.appointment_datetime,a.duration_minutes,a.status from appointments a where a.clinic_id in (select c.id from clinics c where c.clerk_org_id=current_setting('app.clerk_org_id',true)) and (:provider_id is null or a.provider_id=:provider_id) and a.status in ('scheduled','confirmed') and a.appointment_datetime < :end and :start < a.appointment_datetime + (a.duration_minutes * interval '1 minute') order by a.appointment_datetime limit :limit"),{'provider_id':provider_id,'start':start,'end':end,'limit':limit}); return [dict(r._mapping) for r in result]
    async def create(self,data:AppointmentCreate):
        result=await self.session.execute(text("insert into appointments (clinic_id,patient_id,provider_id,provider_name,appointment_datetime,duration_minutes,reason,status) select c.id,:patient_id,:provider_id,:provider_name,:appointment_datetime,:duration_minutes,:reason,'scheduled' from clinics c where c.clerk_org_id=current_setting('app.clerk_org_id',true) and exists(select 1 from patients p where p.id=:patient_id and p.clinic_id=c.id) returning id"),data.model_dump()); row=result.mappings().first()
        if not row: raise ValueError('patient or organization not found')
        return await self.get(row['id'])
    async def update(self,appointment_id:str,data:AppointmentUpdate):
        values=data.model_dump(exclude_unset=True)
        if not values:return await self.get(appointment_id)
        result=await self.session.execute(text("update appointments set status=coalesce(:status,status),reason=coalesce(:reason,reason),appointment_datetime=coalesce(:appointment_datetime,appointment_datetime),duration_minutes=coalesce(:duration_minutes,duration_minutes),provider_id=coalesce(:provider_id,provider_id),provider_name=coalesce(:provider_name,provider_name),updated_at=now() where id=:id and clinic_id in (select c.id from clinics c where c.clerk_org_id=current_setting('app.clerk_org_id',true)) returning id"),{'id':appointment_id,**values}); row=result.mappings().first(); return await self.get(row['id']) if row else None
