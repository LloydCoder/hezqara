from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy import text
from app.core.config import settings
from app.domains.workflows.schemas import WorkflowCreate, WorkflowTrigger
from app.domains.workflows.service import WorkflowService
from app.domains.workflows.runtime import execute_run_sync
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event

router=APIRouter(prefix='/workflows',tags=['workflows'])

@router.get('')
async def list_workflows(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission('workflow:read'))):
    async with tenant_session_context(tenant.organization_id) as session:return await WorkflowService(session).list(limit,offset)

@router.get('/{workflow_id}')
async def get_workflow(workflow_id:str,tenant:TenantContext=Depends(require_permission('workflow:read'))):
    async with tenant_session_context(tenant.organization_id) as session:return await WorkflowService(session).get(workflow_id)

@router.get('/{workflow_id}/runs')
async def list_workflow_runs(workflow_id:str,limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),tenant:TenantContext=Depends(require_permission('workflow:read'))):
    async with tenant_session_context(tenant.organization_id) as session:
        service=WorkflowService(session); clinic=await service.clinic_id(tenant.organization_id); await service.get(workflow_id)
        rows=(await session.execute(text("select id,workflow_version_id,status,trigger_type,actor_id,request_id,idempotency_key,failure_class,retry_count,created_at,started_at,completed_at from workflow_runs where workflow_id=:workflow and clinic_id=:clinic order by created_at desc,id desc limit :limit offset :offset"),{'workflow':workflow_id,'clinic':clinic,'limit':limit,'offset':offset})).mappings()
        return [dict(row) for row in rows]

@router.post('',status_code=201)
async def create_workflow(data:WorkflowCreate,request:Request,tenant:TenantContext=Depends(require_permission('workflow:create'))):
    async with tenant_session_context(tenant.organization_id) as session:
        result=await WorkflowService(session).create(tenant.organization_id,tenant.user_id,data.key,data.name,data.description,data.definition)
        await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action='workflow.created',resource_type='workflow',resource_id=result['id'],outcome='success',request_id=getattr(request.state,'request_id',None))
        return result

@router.post('/{workflow_id}/activate')
async def activate_workflow(workflow_id:str,request:Request,tenant:TenantContext=Depends(require_permission('workflow:activate'))):
    async with tenant_session_context(tenant.organization_id) as session:
        result=await WorkflowService(session).activate(workflow_id)
        await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action='workflow.activated',resource_type='workflow',resource_id=workflow_id,outcome='success',request_id=getattr(request.state,'request_id',None))
        return result

@router.post('/{workflow_id}/runs',status_code=201)
async def trigger_workflow(workflow_id:str,data:WorkflowTrigger,request:Request,tenant:TenantContext=Depends(require_permission('workflow:execute'))):
    async with tenant_session_context(tenant.organization_id) as session:
        run=await WorkflowService(session).trigger(tenant.organization_id,tenant.user_id,workflow_id,data.trigger_type,data.idempotency_key,data.context,getattr(request.state,'request_id',None))
    if run['status']=='queued':
        if settings.redis_url:
            from app.tasks.workflows import execute_workflow_run
            execute_workflow_run.delay(tenant.organization_id,run['id'])
        elif settings.app_env in {'test','development'}:
            run=execute_run_sync(tenant.organization_id,run['id'])
        else:
            raise HTTPException(status_code=503,detail='workflow worker is not configured')
    return run

@router.post('/runs/{run_id}/cancel')
async def cancel_workflow(run_id:str,tenant:TenantContext=Depends(require_permission('workflow:cancel'))):
    async with tenant_session_context(tenant.organization_id) as session:return await WorkflowService(session).transition(tenant.organization_id,run_id,'cancelled')
