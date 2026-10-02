from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.workforce.base.contracts import AgentContext,AgentRequest
from app.workforce.registry import registry
from app.infrastructure.database import tenant_session_context
from app.ai.governance.service import AIGovernanceService

router=APIRouter(prefix="/agents",tags=["agents"])

class ExecuteRequest(BaseModel):
    task:str=Field(min_length=1,max_length=500)
    input:dict=Field(default_factory=dict)
    idempotency_key:str=Field(min_length=8,max_length=200)
    metadata:dict[str,str]=Field(default_factory=dict)

@router.get("")
async def list_agents(tenant:TenantContext=Depends(require_permission("agents:read"))):
    return registry.descriptors()

@router.post("/{agent_name}/execute")
async def execute(agent_name:str,request:ExecuteRequest,http_request:Request,tenant:TenantContext=Depends(require_permission("agents:execute"))):
    try:
        agent=registry.get(agent_name)
    except KeyError as exc:
        raise HTTPException(status_code=404,detail="agent not found") from exc
    async with tenant_session_context(tenant.organization_id) as session:
        governance=AIGovernanceService(session,tenant.organization_id)
        context=AgentContext(
            tenant_id=tenant.organization_id,
            user_id=tenant.user_id,
            permissions=tenant.permissions,
            request_id=getattr(http_request.state,"request_id",None),
            governance=governance,
        )
        return await agent.execute(
            context,
            AgentRequest(
                task=request.task,
                input=request.input,
                idempotency_key=request.idempotency_key,
                metadata=request.metadata,
            ),
        )
