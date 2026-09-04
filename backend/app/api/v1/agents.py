from fastapi import APIRouter, Depends, HTTPException
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.workforce.base.contracts import AgentContext, AgentRequest
from app.workforce.registry import AgentRegistry
from app.ai.orchestration.executor import AgentExecutor
from pydantic import BaseModel
router=APIRouter(prefix="/agents",tags=["agents"])
class ExecuteRequest(BaseModel): task:str; input:dict; idempotency_key:str
registry=AgentRegistry([__import__('app.workforce.reception.agent',fromlist=['ReceptionAgent']).ReceptionAgent(AgentExecutor()),__import__('app.workforce.scheduling.agent',fromlist=['SchedulingAgent']).SchedulingAgent(AgentExecutor())])
@router.get("")
async def list_agents(tenant:TenantContext=Depends(require_permission("agents:read"))): return {"agents":registry.names()}
@router.post("/{agent_name}/execute")
async def execute(agent_name:str,request:ExecuteRequest,tenant:TenantContext=Depends(require_permission("agents:execute"))):
    try: agent=registry.get(agent_name)
    except KeyError: raise HTTPException(status_code=404,detail="agent not found")
    context=AgentContext(tenant_id=tenant.organization_id,user_id=tenant.user_id,permissions=tenant.permissions)
    return await agent.execute(context,AgentRequest(task=request.task,input=request.input,idempotency_key=request.idempotency_key))
