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
    def __init__(self,agents:list[BaseAgent],provider): self._agents={a.name:a for a in agents}; self._provider=provider
    def get(self,name:str)->BaseAgent:
        if name not in self._agents: raise KeyError(f'unknown agent: {name}')
        return self._agents[name]
    def names(self)->list[str]: return sorted(self._agents)
    def descriptors(self)->list[dict[str,str]]:
        provider_configured=self._provider is not None
        status='configured' if provider_configured else 'configuration_required'
        return [{"id":a.name,"name":a.name.replace('_',' ').title(),"status":status,"description":a.description} for a in sorted(self._agents.values(),key=lambda x:x.name)]

def build_registry()->AgentRegistry:
    provider=build_provider(); idempotency=IdempotencyStore(settings.redis_url) if settings.redis_url else None
    executor=AgentExecutor(provider,idempotency=idempotency)
    return AgentRegistry([ReceptionAgent(executor),SchedulingAgent(executor),IntakeAgent(executor),InsuranceAgent(executor),PriorAuthorizationAgent(executor),RefillAgent(executor),RecordsAgent(executor),ReferralsAgent(executor),RecallAgent(executor),EmailAgent(executor)],provider)

registry=build_registry()
