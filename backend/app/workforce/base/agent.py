from app.workforce.base.contracts import AgentContext,AgentRequest,AgentResponse
from app.ai.orchestration.executor import AgentExecutor
from app.workforce.base.policy import PermissionPolicy
class BaseAgent:
    name="base";description="";permission="agents:execute"
    def __init__(self,executor:AgentExecutor):self.executor=executor;self.policy=PermissionPolicy(self.permission)
    async def execute(self,context:AgentContext,request:AgentRequest)->AgentResponse:return await self.executor.execute(self.name,context,request,policy=self.policy,tools=self.tools(context))
    def tools(self,context:AgentContext):return ()
