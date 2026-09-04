from app.workforce.base.agent import BaseAgent

class RefillAgent(BaseAgent):
    name = "refill"
    description = "Intakes refill requests, checks workflow prerequisites and routes medication decisions to authorized clinicians."
    permission = "patients:write"
