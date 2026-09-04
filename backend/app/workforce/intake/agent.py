from app.workforce.base.agent import BaseAgent

class IntakeAgent(BaseAgent):
    name = "intake"
    description = "Collects and validates pre-visit administrative information and routes incomplete intake work."
    permission = "patients:write"
