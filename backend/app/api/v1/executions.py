from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event
from app.workforce.base.contracts import AgentContext,AgentRequest
from app.workforce.registry import registry
from app.domains.executions.repository import ExecutionRepository

router=APIRouter(prefix='/executions',tags=['executions'])
class ExecutionRequest(BaseModel):
    agent_type:str=Field(min_length=1,max_length=100)
    task:str=Field(min_length=1,max_length=500)
    input:dict={}
    idempotency_key:str=Field(min_length=8,max_length=200)

@router.get('')
async def list_executions(limit:int=50,offset:int=0,tenant:TenantContext=Depends(require_permission('executions:read'))):
    if limit<1 or limit>100 or offset<0: raise HTTPException(status_code=400,detail='invalid pagination')
    async with tenant_session_context(tenant.organization_id) as session:
        result=await session.execute(__import__('sqlalchemy').text("select id,actor_id,agent_type,status,provider,model,confidence,escalation_required,result_summary,error_class,started_at,completed_at,created_at,updated_at from agent_executions order by created_at desc,id desc limit :limit offset :offset"),{'limit':limit,'offset':offset})
        return [dict(r._mapping) for r in result]

@router.post('',status_code=202)
async def execute(payload:ExecutionRequest,http_request:Request,tenant:TenantContext=Depends(require_permission('agents:execute'))):
    try: registry.get(payload.agent_type)
    except KeyError as exc: raise HTTPException(status_code=404,detail='agent not found') from exc
    async with tenant_session_context(tenant.organization_id) as session:
        repo=ExecutionRepository(session); existing=await repo.get_by_key(payload.agent_type,payload.idempotency_key)
        if existing:
            if existing['status'] in {'completed','failed','escalated','cancelled'}: return existing
            raise HTTPException(status_code=409,detail='execution already in progress')
        execution=await repo.create(payload.agent_type,tenant.user_id,payload.idempotency_key,payload.task)
        await repo.mark_running(execution['id'])
        await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action='ai.execution.created',resource_type='agent_execution',resource_id=execution['id'],outcome='started',request_id=getattr(http_request.state,'request_id',None))
        context=AgentContext(tenant_id=tenant.organization_id,user_id=tenant.user_id,permissions=tenant.permissions,execution_id=execution['id'],request_id=getattr(http_request.state,'request_id',None))
        try:
            response=await registry.get(payload.agent_type).execute(context,AgentRequest(task=payload.task,input=payload.input,idempotency_key=payload.idempotency_key))
            status=response.status if response.status in {'completed','failed','escalated'} else 'failed'
            await repo.complete(execution['id'],status,response.provider,response.model,response.confidence,response.escalation_required,str(response.output.get('response','')) if isinstance(response.output,dict) else None,None)
            await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action=f'ai.execution.{status}',resource_type='agent_execution',resource_id=execution['id'],outcome=status,request_id=getattr(http_request.state,'request_id',None))
            return {**response.__dict__}
        except Exception as exc:
            await repo.complete(execution['id'],'failed',None,None,None,True,None,type(exc).__name__)
            await append_event(session,organization_id=tenant.organization_id,actor=tenant.user_id,action='ai.execution.failed',resource_type='agent_execution',resource_id=execution['id'],outcome='failed',request_id=getattr(http_request.state,'request_id',None),metadata={'error_class':type(exc).__name__})
            raise HTTPException(status_code=500,detail='AI execution failed') from exc
