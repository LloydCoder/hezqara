from dataclasses import dataclass, field
from typing import Any, Protocol

@dataclass(frozen=True)
class AgentContext:
    tenant_id: str
    user_id: str
    permissions: frozenset[str]
    patient_id: str | None = None
    execution_id: str = ""

@dataclass(frozen=True)
class AgentRequest:
    task: str
    input: dict[str, Any]
    idempotency_key: str

@dataclass(frozen=True)
class AgentResponse:
    status: str
    output: dict[str, Any]
    confidence: float
    escalation_required: bool = False
    execution_id: str = ""

class AgentTool(Protocol):
    name: str
    async def execute(self, context: AgentContext, arguments: dict[str, Any]) -> dict[str, Any]: ...

class AgentPolicy(Protocol):
    def validate(self, context: AgentContext, request: AgentRequest) -> None: ...

class WorkforceAgent(Protocol):
    name: str
    async def execute(self, context: AgentContext, request: AgentRequest) -> AgentResponse: ...
