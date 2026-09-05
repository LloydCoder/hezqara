from app.workforce.base.agent import BaseAgent
from app.workforce.base.policy import PermissionPolicy
class ReferralRecordsAgent(BaseAgent):
    name='referral_records'; description='Referral and records workforce for documentation readiness, routing and administrative follow-up.'; permission='referrals:read'
    def __init__(self,executor): super().__init__(executor); self.policy=PermissionPolicy(self.permission)
