from datetime import datetime
from fastapi import APIRouter,Depends,HTTPException,Query,Request
from sqlalchemy.exc import IntegrityError
from app.domains.scheduling.repository import SchedulingRepository
from app.domains.scheduling.schemas import AppointmentCreate,AppointmentUpdate
from app.domains.scheduling.service import SchedulingService
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event
router=APIRouter(prefix='/appointments',tags=['appointments'])
def conflict(exc:Exception)->bool:
 return 'ExclusionViolationError' in str(exc) or '23P01' in str(exc)
@router.get('')
async def list_appointments(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission('appointments:read'))):
 async with tenant_session_context(tenant.organization_id) as session:return await SchedulingService(SchedulingRepository(session)).list(limit,offset)
@router.get('/availability')
async def availability(start:datetime,end:datetime,provider_id:str|None=None,duration_minutes:int=Query(20,ge=5,le=480),tenant:TenantContext=Depends(require_permission('appointments:read'))):
 if end<=start:raise HTTPException(status_code=422,detail='end must be after start')
 async with tenant_session_context(tenant.organization_id) as session:return await SchedulingService(SchedulingRepository(session)).availability(provider_id,start,end,duration_minutes)
@router.get('/{appointment_id}')
async def get_appointment(appointment_id:str,tenant:TenantContext=Depends(require_permission('appointments:read'))):
 async with tenant_session_context(tenant.organization_id) as session:
  appointment=await SchedulingService(SchedulingRepository(session)).get(appointment_id)
  if not appointment:raise HTTPException(status_code=404,detail='appointment not found')
  return appointment
@router.post('',status_code=201)
async def create_appointment(data:AppointmentCreate,request:Request,tenant:TenantContext=Depends(require_permission('appointments:write'))):
 async with tenant_session_context(tenant.organization_id) as session:
  try:appointment=await SchedulingService(SchedulingRepository(session)).create(data)
  except IntegrityError as exc:
   if conflict(exc):raise HTTPException(status_code=409,detail='appointment conflicts with an existing scheduled appointment') from exc
   raise
  await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action='appointment.created',resource_type='appointment',resource_id=appointment['id'],outcome='success',request_id=getattr(request.state,'request_id',None));return appointment
@router.patch('/{appointment_id}')
async def update_appointment(appointment_id:str,data:AppointmentUpdate,request:Request,tenant:TenantContext=Depends(require_permission('appointments:write'))):
 async with tenant_session_context(tenant.organization_id) as session:
  try:appointment=await SchedulingService(SchedulingRepository(session)).update(appointment_id,data)
  except IntegrityError as exc:
   if conflict(exc):raise HTTPException(status_code=409,detail='appointment conflicts with an existing scheduled appointment') from exc
   raise
  if not appointment:raise HTTPException(status_code=404,detail='appointment not found')
  await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action='appointment.updated',resource_type='appointment',resource_id=appointment_id,outcome='success',request_id=getattr(request.state,'request_id',None),metadata={'status_changed':data.status is not None});return appointment
