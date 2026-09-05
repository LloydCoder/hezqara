import asyncio,json,uuid
from typing import Iterable
from app.ai.evaluation.evaluator import evaluate_output
from app.ai.guardrails.policy import validate_request
from app.ai.prompts.registry import get_prompt
from app.workforce.base.contracts import AgentContext,AgentRequest,AgentResponse,AgentTool,AgentPolicy
from app.security.audit import record
from app.core.config import settings

class AgentExecutor:
    def __init__(self,provider=None,model=None,idempotency=None): self.provider=provider; self.model=model or settings.ai_model; self.idempotency=idempotency
    async def execute(self,agent_name:str,context:AgentContext,request:AgentRequest,*,policy:AgentPolicy|None=None,tools:Iterable[AgentTool]=())->AgentResponse:
        validate_request(context,request)
        if policy: policy.validate(context,request)
        for tool in tools:
            if getattr(tool,'required_permission',None) and tool.required_permission not in context.permissions: raise PermissionError('agent tool permission denied')
        if self.idempotency:
            cached=await self.idempotency.get(context.tenant_id,agent_name,request.idempotency_key)
            if cached:return AgentResponse(**cached)
        execution_id=context.execution_id or str(uuid.uuid4())
        record(tenant=context.tenant_id,actor=context.user_id,action='agent.execute',resource=agent_name,resource_id=execution_id,outcome='started',request_id=context.request_id)
        if self.provider is None:
            return await self._finish(context,agent_name,execution_id,AgentResponse('escalated',{'reason':'AI provider is not configured'},None,True,execution_id),request.idempotency_key)
        schema={'type':'object','required':['action','response','confidence','escalate'],'properties':{'action':{'type':'string'},'response':{'type':'string'},'confidence':{'type':'number'},'escalate':{'type':'boolean'}},'additionalProperties':False}
        last=None
        for attempt in range(2):
            try:
                raw=await asyncio.wait_for(self.provider.structured_output(system_prompt=get_prompt(agent_name).system,user_input=json.dumps({'task':request.task,'input':request.input},ensure_ascii=False,separators=(',',':')),model=self.model,schema=schema),timeout=settings.ai_timeout_seconds)
                confidence=float(raw['confidence']); evaluation=evaluate_output(raw,confidence)
                if not evaluation.valid: raise ValueError('AI output failed deterministic validation')
                escalation=bool(raw.get('escalate')) or confidence<0.7
                response=AgentResponse('escalated' if escalation else 'completed',{'action':str(raw.get('action','')),'response':str(raw.get('response',''))},max(0,min(1,confidence)),escalation,execution_id,getattr(self.provider,'name',None),self.model)
                return await self._finish(context,agent_name,execution_id,response,request.idempotency_key)
            except Exception as exc:
                last=exc; await asyncio.sleep(0.25*(attempt+1))
        record(tenant=context.tenant_id,actor=context.user_id,action='agent.execute',resource=agent_name,resource_id=execution_id,outcome='failed',request_id=context.request_id,metadata={'error':type(last).__name__ if last else 'unknown'})
        return AgentResponse('failed',{'reason':'AI execution failed; human review required'},None,True,execution_id,getattr(self.provider,'name',None),self.model)
    async def _finish(self,context,agent_name,execution_id,response,key=None):
        if self.idempotency and key: await self.idempotency.put(context.tenant_id,agent_name,key,response.__dict__)
        record(tenant=context.tenant_id,actor=context.user_id,action='agent.execute',resource=agent_name,resource_id=execution_id,outcome=response.status,request_id=context.request_id,metadata={'provider':response.provider,'model':response.model,'confidence':response.confidence})
        return response
