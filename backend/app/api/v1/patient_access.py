from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError
from app.domains.patient_access.repository import PatientAccessRepository
from app.domains.patient_access.schemas import AccessRequestCreate, AccessRequestUpdate, IntakeSubmissionCreate, ScheduleCreate, SlotCreate, WaitlistCreate, BookSlotRequest
from app.domains.patient_access.service import PatientAccessService
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event

router=APIRouter(prefix="/patient-access",tags=["patient-access"])

@router.post("/requests",status_code=201)
async def create_request(data:AccessRequestCreate,request:Request,tenant:TenantContext=Depends(require_permission("patients:write"))):
    async with tenant_session_context(tenant.organization_id) as session:
        try: row=await PatientAccessRepository(session).create_access_request(tenant.organization_id,data.model_dump())
        except IntegrityError as exc: raise HTTPException(409,"access request conflicts with existing tenant data") from exc
        await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action="patient_access.request_created",resource_type="patient_access_request",resource_id=row["id"],outcome="success",request_id=getattr(request.state,"request_id",None))
        return row

@router.get("/requests")
async def list_requests(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission("patients:read"))):
    async with tenant_session_context(tenant.organization_id) as session:
        return await PatientAccessRepository(session).list_access_requests(tenant.organization_id,limit,offset)

@router.patch("/requests/{request_id}")
async def update_request(request_id:str,data:AccessRequestUpdate,request:Request,tenant:TenantContext=Depends(require_permission("patients:write"))):
    async with tenant_session_context(tenant.organization_id) as session:
        service=PatientAccessService(PatientAccessRepository(session))
        row=await service.update_access_request(tenant.organization_id,request_id,data.status)
        await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action="patient_access.request_status_changed",resource_type="patient_access_request",resource_id=request_id,outcome="success",request_id=getattr(request.state,"request_id",None),metadata={"status":data.status})
        return row

@router.post("/intake",status_code=201)
async def submit_intake(data:IntakeSubmissionCreate,request:Request,tenant:TenantContext=Depends(require_permission("patients:write"))):
    async with tenant_session_context(tenant.organization_id) as session:
        try: row=await PatientAccessRepository(session).create_intake(tenant.organization_id,data.model_dump(),tenant.user_id)
        except IntegrityError as exc: raise HTTPException(409,"intake references data outside the tenant") from exc
        await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action="patient_access.intake_created",resource_type="patient_intake_submission",resource_id=row["id"],outcome="success",request_id=getattr(request.state,"request_id",None),metadata={"status":row["status"]})
        return row

@router.get("/intake/{patient_id}")
async def list_intake(patient_id:str,tenant:TenantContext=Depends(require_permission("patients:read"))):
    async with tenant_session_context(tenant.organization_id) as session:
        return await PatientAccessRepository(session).list_intake(tenant.organization_id,patient_id)

@router.post("/schedules",status_code=201)
async def create_schedule(data:ScheduleCreate,request:Request,tenant:TenantContext=Depends(require_permission("appointments:write"))):
    async with tenant_session_context(tenant.organization_id) as session:
        row=await PatientAccessRepository(session).create_schedule(tenant.organization_id,data.model_dump())
        await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action="patient_access.schedule_created",resource_type="provider_schedule",resource_id=row["id"],outcome="success",request_id=getattr(request.state,"request_id",None))
        return row

@router.post("/schedules/{schedule_id}/slots",status_code=201)
async def create_slot(schedule_id:str,data:SlotCreate,request:Request,tenant:TenantContext=Depends(require_permission("appointments:write"))):
    if data.ends_at <= data.starts_at: raise HTTPException(422,"ends_at must be after starts_at")
    async with tenant_session_context(tenant.organization_id) as session:
        try: row=await PatientAccessRepository(session).create_slot(tenant.organization_id,schedule_id,data.model_dump())
        except ValueError as exc: raise HTTPException(404,str(exc)) from exc
        await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action="patient_access.slot_created",resource_type="schedule_slot",resource_id=row["id"],outcome="success",request_id=getattr(request.state,"request_id",None))
        return row

@router.get("/schedules/{schedule_id}/slots")
async def list_slots(schedule_id:str,start:datetime,end:datetime,tenant:TenantContext=Depends(require_permission("appointments:read"))):
    if end <= start: raise HTTPException(422,"end must be after start")
    async with tenant_session_context(tenant.organization_id) as session:
        return await PatientAccessRepository(session).list_slots(tenant.organization_id,schedule_id,start,end)

@router.post("/waitlist",status_code=201)
async def create_waitlist(data:WaitlistCreate,request:Request,tenant:TenantContext=Depends(require_permission("appointments:write"))):
    async with tenant_session_context(tenant.organization_id) as session:
        try: row=await PatientAccessRepository(session).create_waitlist(tenant.organization_id,data.model_dump())
        except IntegrityError as exc: raise HTTPException(409,"waitlist references data outside the tenant") from exc
        await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action="patient_access.waitlist_created",resource_type="waitlist_entry",resource_id=row["id"],outcome="success",request_id=getattr(request.state,"request_id",None))
        return row

@router.post("/slots/{slot_id}/book",status_code=201)
async def book_slot(slot_id:str,data:BookSlotRequest,request:Request,tenant:TenantContext=Depends(require_permission("appointments:write"))):
    async with tenant_session_context(tenant.organization_id) as session:
        try: row=await PatientAccessRepository(session).book_slot(tenant.organization_id,slot_id,data.patient_id,data.reason)
        except ValueError as exc: raise HTTPException(404,str(exc)) from exc
        except RuntimeError as exc: raise HTTPException(409,str(exc)) from exc
        except IntegrityError as exc: raise HTTPException(409,"booking references data outside the tenant") from exc
        await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action="patient_access.slot_booked",resource_type="appointment",resource_id=row["id"],outcome="success",request_id=getattr(request.state,"request_id",None),metadata={"slot_id":slot_id})
        return row
