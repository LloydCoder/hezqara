from fastapi import HTTPException
from app.domains.scheduling.repository import SchedulingRepository
from app.domains.scheduling.schemas import AppointmentCreate,AppointmentUpdate

_ALLOWED={'scheduled':{'confirmed','cancelled','no_show'},'confirmed':{'completed','cancelled','no_show'},'completed':set(),'cancelled':set(),'no_show':set()}
class SchedulingService:
    def __init__(self,repo:SchedulingRepository): self.repo=repo
    async def list(self,limit:int,offset:int): return await self.repo.list(limit,offset)
    async def get(self,appointment_id:str): return await self.repo.get(appointment_id)
    async def availability(self,provider_id,start,end,duration_minutes:int): return await self.repo.availability(provider_id,start,end,duration_minutes)
    async def create(self,data:AppointmentCreate): return await self.repo.create(data)
    async def update(self,appointment_id:str,data:AppointmentUpdate):
        current=await self.repo.get(appointment_id)
        if not current: raise HTTPException(status_code=404,detail='appointment not found')
        if data.status and data.status!=current['status'] and data.status not in _ALLOWED[current['status']]: raise HTTPException(status_code=409,detail='invalid appointment state transition')
        if current['status'] in {'completed','cancelled','no_show'} and any(v is not None for k,v in data.model_dump(exclude_unset=True).items() if k!='status'): raise HTTPException(status_code=409,detail='terminal appointment cannot be rescheduled or edited')
        return await self.repo.update(appointment_id,data)
