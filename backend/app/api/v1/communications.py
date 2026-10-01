from fastapi import APIRouter,Depends,Query,Request,HTTPException
from sqlalchemy import text
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event
from app.domains.patient_engagement.schemas import CommunicationCreate,CommunicationPreferenceUpdate,MessageIntake
from app.domains.patient_engagement.service import CommunicationService
from app.domains.patient_engagement.providers import build_communication_provider
from app.domains.patient_engagement.ai import MessageIntelligence
from app.ai.governance.service import AIGovernanceService
router=APIRouter(prefix='/communications',tags=['communications'])
@router.get('')
async def list_communications(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission('communications:read'))):
    async with tenant_session_context(tenant.organization_id) as session:
        rows=(await session.execute(text('select id,patient_id,appointment_id,workflow_run_id,channel,direction,status,subject,body,template_key,provider_reference,failure_class,idempotency_key,correlation_id,created_at,updated_at,sent_at,delivered_at from communications order by created_at desc,id desc limit :limit offset :offset'),{'limit':limit,'offset':offset})).mappings(); return [dict(r) for r in rows]
@router.get('/patients/{patient_id}/preferences')
async def get_preferences(patient_id:str,tenant:TenantContext=Depends(require_permission('communications:read'))):
    async with tenant_session_context(tenant.organization_id) as session:
        row=(await session.execute(text("select p.id,p.patient_id,p.sms_enabled,p.email_enabled,p.whatsapp_enabled,p.opted_out_all,p.timezone,p.updated_at from patient_communication_preferences p where p.patient_id=:patient and p.clinic_id in (select id from clinics where clerk_org_id=current_setting('app.clerk_org_id',true))"),{'patient':patient_id})).mappings().first(); return dict(row) if row else {'patient_id':patient_id,'sms_enabled':True,'email_enabled':True,'whatsapp_enabled':False,'opted_out_all':False,'timezone':'UTC'}
@router.put('/patients/{patient_id}/preferences')
async def set_preferences(patient_id:str,data:CommunicationPreferenceUpdate,request:Request,tenant:TenantContext=Depends(require_permission('communications:write'))):
    async with tenant_session_context(tenant.organization_id) as session:
        result=await CommunicationService(session,build_communication_provider()).preferences(tenant.organization_id,patient_id,data); await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action='communication.preferences.updated',resource_type='patient',resource_id=patient_id,outcome='success',request_id=getattr(request.state,'request_id',None)); return result
@router.post('',status_code=201)
async def create_communication(data:CommunicationCreate,request:Request,tenant:TenantContext=Depends(require_permission('communications:send'))):
    async with tenant_session_context(tenant.organization_id) as session:
        result=await CommunicationService(session,build_communication_provider()).queue(tenant.organization_id,data,getattr(request.state,'request_id',None)); await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action='communication.queued',resource_type='communication',resource_id=result['id'],outcome=result['status'],request_id=getattr(request.state,'request_id',None)); return result
@router.post('/intake')
async def classify_message(data:MessageIntake,tenant:TenantContext=Depends(require_permission('communications:read'))):
    async with tenant_session_context(tenant.organization_id) as session:
        patient=(await session.execute(text('select id from patients where id=:id and clinic_id in (select id from clinics where clerk_org_id=current_setting(\'app.clerk_org_id\',true))'),{'id':data.patient_id})).scalar_one_or_none()
        if not patient:raise HTTPException(status_code=404,detail='patient not found')
        governance=AIGovernanceService(session,tenant.organization_id)
        try:
            return await MessageIntelligence().classify(data.message,governance=governance)
        except RuntimeError as exc:
            detail=str(exc)
            if 'provider is not configured' in detail:
                raise HTTPException(status_code=503,detail='AI provider is not configured') from exc
            raise HTTPException(status_code=403,detail='AI message classification blocked by governance') from exc
