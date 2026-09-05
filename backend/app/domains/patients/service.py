from app.domains.patients.repository import PatientRepository
from app.domains.patients.schemas import PatientCreate, PatientUpdate

class PatientService:
    def __init__(self, repo: PatientRepository):
        self.repo = repo
    async def list(self, limit: int, offset: int, search: str = ""):
        return await self.repo.list(limit, offset, search)
    async def get(self, patient_id: str):
        return await self.repo.get(patient_id)
    async def create(self, data: PatientCreate):
        return await self.repo.create(data)
    async def update(self, patient_id: str, data: PatientUpdate):
        return await self.repo.update(patient_id, data)
