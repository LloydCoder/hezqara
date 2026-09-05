from app.workforce.base.agent import BaseAgent
from app.workforce.base.policy import PermissionPolicy

class RevenueCycleAgent(BaseAgent):
    name='revenue_cycle'; description='Revenue-cycle administrative workforce for billing, claims, denials and A/R.'; permission='claims:read'
    def __init__(self,executor): super().__init__(executor); self.policy=PermissionPolicy(self.permission)
