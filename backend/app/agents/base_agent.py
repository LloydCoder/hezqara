"""
BaseAgent — Abstract foundation for all Carenova agents.

All 9 agents (Reception, Scheduling, Intake, Insurance,
Prior Auth, Refill, Records, Referrals, Recall) inherit this.

Rules enforced here:
  - Every agent must have a clinic_id
  - Every agent must have an agent_type
  - Every agent routes LLM calls through the gateway
  - Every agent uses Graphiti for persistent memory
  - HIPAA audit logging is available to all agents
"""
from abc import ABC, abstractmethod
from typing import Optional, Any


class BaseAgent(ABC):
    """
    Abstract base class for all Carenova AI agents.

    Subclasses must define:
        - agent_type (class attribute)

    Subclasses receive:
        - self.clinic_id
        - self.llm (LLMGateway — injected)
        - self.memory (GraphitiClient — injected)
        - self.ehr (EHR client — injected, optional)
    """

    agent_type: str = "base"

    def __init__(
        self,
        clinic_id: str,
        llm: Optional[Any] = None,
        memory: Optional[Any] = None,
        ehr: Optional[Any] = None,
    ) -> None:
        if not clinic_id:
            raise ValueError("clinic_id is required")

        self.clinic_id = clinic_id
        self.llm = llm
        self.memory = memory
        self.ehr = ehr

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} clinic_id={self.clinic_id}>"
