from app.workforce.base.agent import BaseAgent

class RecordsAgent(BaseAgent):
    name = "records"
    description = "Coordinates medical-record request workflows, validates administrative requirements and tracks fulfillment."
    permission = "patients:read"
