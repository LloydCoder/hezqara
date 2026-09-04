import json
import uuid
from app.ai.guardrails.policy import validate_request
from app.ai.prompts.registry import get_prompt
from app.workforce.base.contracts import AgentContext, AgentRequest, AgentResponse
from app.security.audit import record

class AgentExecutor:
    def __init__(self, provider=None, model=None, idempotency=None): self.provider=provider; self.model=model; self.idempotency=idempotency
    async def execute(self, agent_name: str, context: AgentContext, request: AgentRequest) -> AgentResponse:
        validate_request(context, request)
        if self.idempotency:
            cached = await self.idempotency.get(context.tenant_id, request.idempotency_key)
            if cached: return AgentResponse(**cached)
        execution_id=str(uuid.uuid4())
        record(tenant=context.tenant_id,actor=context.user_id,action="agent.execute",resource=agent_name,resource_id=None,outcome="started",metadata={"execution_id":execution_id})
        if self.provider is None:
            response=AgentResponse(status="escalated",output={"reason":"no model provider configured"},confidence=0.0,escalation_required=True,execution_id=execution_id)
        else:
            result=await self.provider.structured_output(system_prompt=get_prompt(agent_name).system,user_input=json.dumps(request.input,ensure_ascii=False,separators=(",",":")),model=self.model,schema={"type":"object","required":["action","response","confidence","escalate"],"properties":{"action":{"type":"string"},"response":{"type":"string"},"confidence":{"type":"number"},"escalate":{"type":"boolean"}}})
            confidence=float(result.get("confidence",0.0))
            if not 0.0<=confidence<=1.0: raise ValueError("model confidence outside allowed range")
            escalation=bool(result.get("escalate",False)) or confidence<0.7
            response=AgentResponse(status="escalated" if escalation else "completed",output={"action":str(result.get("action","")),"response":str(result.get("response",""))},confidence=confidence,escalation_required=escalation,execution_id=execution_id)
        if self.idempotency: await self.idempotency.put(context.tenant_id,request.idempotency_key,{"status":response.status,"output":response.output,"confidence":response.confidence,"escalation_required":response.escalation_required,"execution_id":response.execution_id})
        record(tenant=context.tenant_id,actor=context.user_id,action="agent.execute",resource=agent_name,resource_id=None,outcome=response.status,metadata={"execution_id":execution_id,"confidence":response.confidence})
        return response
