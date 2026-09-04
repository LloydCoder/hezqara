import uuid
from app.ai.guardrails.policy import validate_request
from app.workforce.base.contracts import AgentContext, AgentRequest, AgentResponse
from app.security.audit import record
class AgentExecutor:
    def __init__(self, provider=None): self.provider=provider
    async def execute(self, agent_name:str, context:AgentContext, request:AgentRequest)->AgentResponse:
        validate_request(context,request)
        execution_id=str(uuid.uuid4())
        record(tenant=context.tenant_id,actor=context.user_id,action="agent.execute",resource=agent_name,resource_id=None,outcome="started")
        if self.provider is None:
            return AgentResponse(status="escalated",output={"reason":"no model provider configured"},confidence=0.0,escalation_required=True,execution_id=execution_id)
        raise RuntimeError("provider/tool policy execution must be supplied by the concrete agent")
