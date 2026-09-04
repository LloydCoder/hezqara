from app.workforce.base.agent import BaseAgent

class RecallAgent(BaseAgent):
    name = "recall"
    description = "Builds authorized patient-recall work queues and prepares outreach tasks without inventing clinical recommendations."
    permission = "patients:write"
