from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.workforce.base.contracts import AgentContext,AgentRequest
from app.workforce.registry import registry
router=APIRouter(prefix="/agents",tags=["agents"])
class ExecuteRequest(BaseModel):task:str=Field(min_length=1,max_length=200);input:dict=Field(default_factory=dict);idempotency_key:str=Field(min_length=8,max_length=200)
@router.get("")
async def list_agents(tenant:TenantContext=Depends(require_permission("agents:read"))):
    return registry.descriptors()
@router.post("/{agent_name}/execute")
async def execute(agent_name:str,request:ExecuteRequest,tenant:TenantContext=Depends(require_permission("agents:execute"))):
    try:agent=registry.get(agent_name)
    except KeyError as exc:raise HTTPException(status_code=404,detail="agent not found") from exc
    context=AgentContext(tenant_id=tenant.organization_id,user_id=tenant.user_id,permissions=tenant.permissions)
    return await agent.execute(context,AgentRequest(task=request.task,input=request.input,idempotency_key=request.idempotency_key))
