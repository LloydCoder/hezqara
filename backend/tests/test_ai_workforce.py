import pytest
from app.ai.orchestration.executor import AgentExecutor
from app.workforce.base.contracts import AgentContext,AgentRequest
from app.workforce.base.policy import PermissionPolicy

class FakeProvider:
    name="fake"
    async def structured_output(self,**kwargs):
        return {"action":"draft_response","response":"safe","confidence":0.92,"escalate":False}

@pytest.mark.asyncio
async def test_agent_execution_requires_permission():
    executor=AgentExecutor(FakeProvider(),model="test")
    context=AgentContext("org-a","user-a",frozenset())
    request=AgentRequest("reply",{},"idem-1234")
    with pytest.raises(PermissionError): await executor.execute("reception",context,request,policy=PermissionPolicy("agents:execute"))

@pytest.mark.asyncio
async def test_agent_execution_is_structured_and_auditable_contract():
    executor=AgentExecutor(FakeProvider(),model="test")
    context=AgentContext("org-a","user-a",frozenset({"agents:execute"}),request_id="req-1")
    request=AgentRequest("reply",{"message":"hello"},"idem-5678")
    result=await executor.execute("reception",context,request,policy=PermissionPolicy("agents:execute"))
    assert result.status=="completed" and result.confidence==0.92 and result.execution_id
