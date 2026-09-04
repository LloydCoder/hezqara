from app.workforce.base.contracts import AgentContext,AgentRequest,AgentResponse
from app.ai.orchestration.executor import AgentExecutor
from app.workforce.base.policy import PermissionPolicy
class BaseAgent:
    name="base";description="";permission="agents:execute"
    def __init__(self,executor:AgentExecutor):self.executor=executor;self.policy=PermissionPolicy(self.permission)
    async def execute(self,context:AgentContext,request:AgentRequest)->AgentResponse:self.policy.validate(context,request);return await self.executor.execute(self.name,context,request)
