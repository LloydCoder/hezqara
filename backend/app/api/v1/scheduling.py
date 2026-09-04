from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import tenant_session,tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.domains.scheduling.repository import SchedulingRepository
from app.domains.scheduling.schemas import AppointmentCreate
from app.domains.scheduling.service import SchedulingService
router=APIRouter(prefix="/appointments",tags=["scheduling"])
async def db(tenant:TenantContext=Depends(require_permission("appointments:read"))):
    async for session in tenant_session(tenant.organization_id): yield session
@router.get("")
async def list_appointments(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),session:AsyncSession=Depends(db)):
    return await SchedulingService(SchedulingRepository(session)).list(limit,offset)
@router.post("",status_code=201)
async def create_appointment(data:AppointmentCreate,tenant:TenantContext=Depends(require_permission("appointments:write"))):
    async with tenant_session_context(tenant.organization_id) as session:
        return await SchedulingService(SchedulingRepository(session)).create(data)
