from app.ai.orchestration.executor import AgentExecutor
from app.ai.orchestration.idempotency import IdempotencyStore
from app.ai.providers.factory import build_provider
from app.core.config import settings
from app.workforce.base.agent import BaseAgent
from app.workforce.reception.agent import ReceptionAgent
from app.workforce.scheduling.agent import SchedulingAgent
from app.workforce.intake.agent import IntakeAgent
from app.workforce.insurance.agent import InsuranceAgent
from app.workforce.prior_authorization.agent import PriorAuthorizationAgent
from app.workforce.refill.agent import RefillAgent
from app.workforce.records.agent import RecordsAgent
from app.workforce.referrals.agent import ReferralsAgent
from app.workforce.recall.agent import RecallAgent
from app.workforce.email.agent import EmailAgent

class AgentRegistry:
    def __init__(self, agents: list[BaseAgent]): self._agents={a.name:a for a in agents}
    def get(self,name:str)->BaseAgent:
        if name not in self._agents: raise KeyError(f"unknown agent: {name}")
        return self._agents[name]
    def names(self): return sorted(self._agents)

def build_registry() -> AgentRegistry:
    idempotency = IdempotencyStore() if settings.redis_url else None
    executor=AgentExecutor(build_provider(),idempotency=idempotency)
    return AgentRegistry([ReceptionAgent(executor),SchedulingAgent(executor),IntakeAgent(executor),InsuranceAgent(executor),PriorAuthorizationAgent(executor),RefillAgent(executor),RecordsAgent(executor),ReferralsAgent(executor),RecallAgent(executor),EmailAgent(executor)])

registry=build_registry()
