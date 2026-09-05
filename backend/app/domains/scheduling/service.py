from app.domains.scheduling.repository import SchedulingRepository
from app.domains.scheduling.schemas import AppointmentCreate,AppointmentUpdate
from fastapi import HTTPException
class SchedulingService:
    def __init__(self,repo:SchedulingRepository):self.repo=repo
    async def list(self,limit:int,offset:int):return await self.repo.list(limit,offset)
    async def get(self,appointment_id:str):return await self.repo.get(appointment_id)
    async def create(self,data:AppointmentCreate):return await self.repo.create(data)
    async def update(self,appointment_id:str,data:AppointmentUpdate):
        current=await self.repo.get(appointment_id)
        if not current:raise HTTPException(status_code=404,detail='appointment not found')
        if data.status=='completed' and current['status'] in {'cancelled','no_show'}:raise HTTPException(status_code=409,detail='invalid appointment state transition')
        if data.status=='cancelled' and current['status']=='completed':raise HTTPException(status_code=409,detail='invalid appointment state transition')
        return await self.repo.update(appointment_id,data)
