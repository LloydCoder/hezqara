from app.workforce.base.agent import BaseAgent

class EmailAgent(BaseAgent):
    name = "email"
    description = "Triages operational inbox work and drafts patient communications subject to authorization and review policy."
    permission = "patients:write"
