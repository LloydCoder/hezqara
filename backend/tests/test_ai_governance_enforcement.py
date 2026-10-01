import pytest

from app.ai.governance.contracts import GovernanceDecision
from app.ai.orchestration.executor import AgentExecutor
from app.domains.patient_engagement.ai import MessageIntelligence
from app.workforce.base.contracts import AgentContext, AgentRequest


class FakeProvider:
    name = "fake"

    def __init__(self, output=None):
        self.calls = 0
        self.output = output or {"action": "draft_response", "response": "safe", "confidence": 0.95, "escalate": False}

    async def structured_output(self, **kwargs):
        self.calls += 1
        return self.output


class FakeGovernance:
    def __init__(self, initial="allow", post="allow", tool="allow"):
        self.initial = initial
        self.post = post
        self.tool = tool
        self.calls = []

    def _decision(self, value, reason="test"):
        return GovernanceDecision(
            decision=value,
            risk_tier=1,
            capability_id="reception",
            capability_version="1",
            policy_version_id=1,
            reason=reason,
            allowed_actions=("draft_response",),
            allowed_data_classes=("operational",),
            allowed_tools=("send_message",),
            approval_required=value == "approval_required",
            escalation_required=value in {"approval_required", "escalate"},
            failure_category="POLICY_DENIED" if value == "deny" else None,
            policy_version="1",
            prompt_version="1",
        )

    async def resolve_execution_policy(self, capability_id, action, provider, confidence=None, **kwargs):
        self.calls.append(("resolve", capability_id, action, provider, tuple(kwargs.get("tools", ()))))
        value = self.initial if action is None else self.post
        return self._decision(value)

    async def authorize_side_effect(self, execution_id, capability_id, action, provider=None, confidence=None, **kwargs):
        self.calls.append(("side_effect", capability_id, action, provider))
        return self._decision(self.tool)


@pytest.mark.asyncio
async def test_agent_execution_fails_closed_without_governance():
    executor = AgentExecutor(FakeProvider(), model="test")
    context = AgentContext("org-a", "user-a", frozenset({"agents:execute"}))
    request = AgentRequest("reply", {}, "idem-no-governance")
    with pytest.raises(RuntimeError, match="governance"):
        await executor.execute("reception", context, request)


@pytest.mark.asyncio
async def test_policy_deny_happens_before_model_call():
    provider = FakeProvider()
    governance = FakeGovernance(initial="deny")
    executor = AgentExecutor(provider, model="test")
    context = AgentContext("org-a", "user-a", frozenset({"agents:execute"}), governance=governance)
    request = AgentRequest("reply", {}, "idem-policy-deny")
    result = await executor.execute("reception", context, request)
    assert result.status == "escalated"
    assert provider.calls == 0
    assert governance.calls[0][0:3] == ("resolve", "reception", None)


@pytest.mark.asyncio
async def test_pre_model_approval_requirement_allows_safe_proposal_generation():
    provider = FakeProvider()
    governance = FakeGovernance(initial="approval_required", post="approval_required")
    executor = AgentExecutor(provider, model="test")
    context = AgentContext("org-a", "user-a", frozenset({"agents:execute"}), execution_id="exec-proposal", governance=governance)
    request = AgentRequest("reply", {}, "idem-proposal")
    result = await executor.execute("reception", context, request)
    assert provider.calls == 1
    assert result.status == "escalated"
    assert result.output["governance_decision"] == "approval_required"


@pytest.mark.asyncio
async def test_model_output_cannot_bypass_post_execution_policy():
    provider = FakeProvider()
    governance = FakeGovernance(post="approval_required")
    executor = AgentExecutor(provider, model="test")
    context = AgentContext("org-a", "user-a", frozenset({"agents:execute"}), execution_id="exec-1", governance=governance)
    request = AgentRequest("reply", {}, "idem-approval")
    result = await executor.execute("reception", context, request)
    assert provider.calls == 1
    assert result.status == "escalated"
    assert result.output["governance_decision"] == "approval_required"


@pytest.mark.asyncio
async def test_governed_tool_call_requires_allow_decision():
    class Tool:
        name = "send_message"
        required_permission = "messages:send"

        async def execute(self, context, arguments):
            return {"sent": True}

    provider = FakeProvider()
    governance = FakeGovernance(tool="deny")
    executor = AgentExecutor(provider, model="test")
    context = AgentContext(
        "org-a",
        "user-a",
        frozenset({"agents:execute", "messages:send"}),
        execution_id="exec-tool",
        governance=governance,
    )
    result = await executor.execute_tool(
        context,
        Tool(),
        {"message": "hello"},
        capability_id="reception",
        action="send_message",
    )
    assert result["status"] == "blocked"
    assert result["failure_category"] == "POLICY_DENIED"


@pytest.mark.asyncio
async def test_message_intelligence_requires_governance():
    with pytest.raises(RuntimeError, match="governance"):
        await MessageIntelligence().classify("confirm my appointment")


@pytest.mark.asyncio
async def test_message_intelligence_cannot_classify_clinical_content_without_human_review(monkeypatch):
    monkeypatch.setattr("app.domains.patient_engagement.ai.settings.app_env", "test")
    governance = FakeGovernance()
    result = await MessageIntelligence().classify("I have chest pain", governance=governance)
    assert result.intent == "clinical"
    assert result.requires_human is True
    assert result.safe_to_draft is False
