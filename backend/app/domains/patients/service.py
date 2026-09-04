from app.domains.patients.repository import PatientRepository
from app.domains.patients.schemas import PatientCreate
class PatientService:
    def __init__(self,repo:PatientRepository):self.repo=repo
    async def list(self,limit:int,offset:int,search:str=""):return await self.repo.list(limit,offset,search)
    async def create(self,data:PatientCreate):return await self.repo.create(data)
