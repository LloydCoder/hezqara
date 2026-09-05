from app.workforce.base.agent import BaseAgent
from app.workforce.base.policy import PermissionPolicy
class InsuranceAdministrativeAgent(BaseAgent):
    name='insurance_administrative'; description='Insurance workforce for coverage normalization, eligibility readiness and authorization information gaps.'; permission='insurance:read'
    def __init__(self,executor): super().__init__(executor); self.policy=PermissionPolicy(self.permission)
