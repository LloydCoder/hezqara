from app.workforce.base.agent import BaseAgent

class InsuranceAgent(BaseAgent):
    name = "insurance"
    description = "Supports eligibility, benefits, coverage verification and insurance-workqueue preparation."
    permission = "insurance:write"
