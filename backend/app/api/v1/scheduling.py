from fastapi import APIRouter, Depends, HTTPException, Query, Request
from app.domains.scheduling.repository import SchedulingRepository
from app.domains.scheduling.schemas import AppointmentCreate
from app.domains.scheduling.service import SchedulingService
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event

router=APIRouter(prefix='/appointments',tags=['appointments'])

@router.get('')
async def list_appointments(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission('appointments:read'))):
    async with tenant_session_context(tenant.organization_id) as session:
        return await SchedulingService(SchedulingRepository(session)).list(limit,offset)

@router.get('/{appointment_id}')
async def get_appointment(appointment_id:str,tenant:TenantContext=Depends(require_permission('appointments:read'))):
    async with tenant_session_context(tenant.organization_id) as session:
        appointment=await SchedulingService(SchedulingRepository(session)).get(appointment_id)
        if not appointment: raise HTTPException(status_code=404,detail='appointment not found')
        return appointment

@router.post('',status_code=201)
async def create_appointment(data:AppointmentCreate,request:Request,tenant:TenantContext=Depends(require_permission('appointments:write'))):
    async with tenant_session_context(tenant.organization_id) as session:
        appointment=await SchedulingService(SchedulingRepository(session)).create(data)
        await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action='appointment.created',resource_type='appointment',resource_id=appointment['id'],outcome='success',request_id=getattr(request.state,'request_id',None))
        return appointment
