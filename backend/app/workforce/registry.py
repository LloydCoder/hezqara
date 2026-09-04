from app.workforce.base.agent import BaseAgent
class AgentRegistry:
    def __init__(self, agents: list[BaseAgent]): self._agents={a.name:a for a in agents}
    def get(self,name:str)->BaseAgent:
        try:return self._agents[name]
        except KeyError: raise KeyError(f"unknown agent: {name}")
    def names(self): return sorted(self._agents)
