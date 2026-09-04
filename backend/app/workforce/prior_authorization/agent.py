from app.workforce.base.agent import BaseAgent

class PriorAuthorizationAgent(BaseAgent):
    name = "prior_authorization"
    description = "Prepares prior-authorization work, identifies missing administrative evidence and escalates clinical determinations."
    permission = "insurance:write"
