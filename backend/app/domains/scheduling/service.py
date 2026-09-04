from app.domains.scheduling.repository import SchedulingRepository
from app.domains.scheduling.schemas import AppointmentCreate
class SchedulingService:
    def __init__(self,repo:SchedulingRepository): self.repo=repo
    async def list(self,limit:int,offset:int): return await self.repo.list(limit,offset)
    async def create(self,data:AppointmentCreate): return await self.repo.create(data)
