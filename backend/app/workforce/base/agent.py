from app.workforce.base.contracts import AgentContext, AgentRequest, AgentResponse
from app.ai.orchestration.executor import AgentExecutor
class BaseAgent:
    name = "base"
    def __init__(self, executor: AgentExecutor): self.executor=executor
    async def execute(self, context:AgentContext, request:AgentRequest)->AgentResponse:
        return await self.executor.execute(self.name, context, request)
