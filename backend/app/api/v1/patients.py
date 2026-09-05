from fastapi import APIRouter, Depends, HTTPException, Query, Request
from app.domains.patients.repository import PatientRepository
from app.domains.patients.schemas import PatientCreate, PatientUpdate
from app.domains.patients.service import PatientService
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event

router=APIRouter(prefix='/patients',tags=['patients'])

@router.get('')
async def list_patients(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),search:str=Query('',max_length=100),tenant:TenantContext=Depends(require_permission('patients:read'))):
    async with tenant_session_context(tenant.organization_id) as session:
        return await PatientService(PatientRepository(session)).list(limit,offset,search)

@router.get('/{patient_id}')
async def get_patient(patient_id:str,tenant:TenantContext=Depends(require_permission('patients:read'))):
    async with tenant_session_context(tenant.organization_id) as session:
        patient=await PatientService(PatientRepository(session)).get(patient_id)
        if not patient: raise HTTPException(status_code=404,detail='patient not found')
        return patient

@router.post('',status_code=201)
async def create_patient(data:PatientCreate,request:Request,tenant:TenantContext=Depends(require_permission('patients:write'))):
    async with tenant_session_context(tenant.organization_id) as session:
        patient=await PatientService(PatientRepository(session)).create(data)
        await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action='patient.created',resource_type='patient',resource_id=patient['id'],outcome='success',request_id=getattr(request.state,'request_id',None))
        return patient

@router.patch('/{patient_id}')
async def update_patient(patient_id:str,data:PatientUpdate,request:Request,tenant:TenantContext=Depends(require_permission('patients:write'))):
    async with tenant_session_context(tenant.organization_id) as session:
        patient=await PatientService(PatientRepository(session)).update(patient_id,data)
        if not patient: raise HTTPException(status_code=404,detail='patient not found')
        await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action='patient.updated',resource_type='patient',resource_id=patient_id,outcome='success',request_id=getattr(request.state,'request_id',None))
        return patient
