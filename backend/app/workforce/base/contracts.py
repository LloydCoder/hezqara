from dataclasses import dataclass, field
from typing import Any, Protocol

@dataclass(frozen=True)
class AgentContext:
    tenant_id:str
    user_id:str
    permissions:frozenset[str]
    patient_id:str|None=None
    execution_id:str=''
    request_id:str|None=None
    governance:Any|None=None

@dataclass(frozen=True)
class AgentRequest:
    task:str
    input:dict[str,Any]
    idempotency_key:str
    metadata:dict[str,str]=field(default_factory=dict)

@dataclass(frozen=True)
class AgentResponse:
    status:str
    output:dict[str,Any]
    confidence:float|None
    escalation_required:bool=False
    execution_id:str=''
    provider:str|None=None
    model:str|None=None

class AgentTool(Protocol):
    name:str
    required_permission:str
    async def execute(self,context:AgentContext,arguments:dict[str,Any])->dict[str,Any]: ...

class AgentPolicy(Protocol):
    def validate(self,context:AgentContext,request:AgentRequest)->None: ...

class WorkforceAgent(Protocol):
    name:str
    required_permission:str
    async def execute(self,context:AgentContext,request:AgentRequest)->AgentResponse: ...
