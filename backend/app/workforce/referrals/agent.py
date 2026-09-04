from app.workforce.base.agent import BaseAgent

class ReferralsAgent(BaseAgent):
    name = "referrals"
    description = "Creates and tracks referral workflow tasks while escalating clinical referral decisions to authorized staff."
    permission = "patients:write"
