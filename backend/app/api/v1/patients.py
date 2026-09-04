from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import tenant_session,tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.domains.patients.repository import PatientRepository
from app.domains.patients.schemas import PatientCreate
from app.domains.patients.service import PatientService
router=APIRouter(prefix="/patients",tags=["patients"])
async def db(tenant:TenantContext=Depends(require_permission("patients:read"))):
    async for session in tenant_session(tenant.organization_id): yield session
@router.get("")
async def list_patients(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),session:AsyncSession=Depends(db)):
    return await PatientService(PatientRepository(session)).list(limit,offset)
@router.post("",status_code=201)
async def create_patient(data:PatientCreate,tenant:TenantContext=Depends(require_permission("patients:write"))):
    async with tenant_session_context(tenant.organization_id) as session:
        return await PatientService(PatientRepository(session)).create(data)
