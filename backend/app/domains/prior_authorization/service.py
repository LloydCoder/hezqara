from app.domains.prior_authorization.schemas import PriorAuthorizationRequest,PriorAuthorizationResult
class PriorAuthorizationService:
    def __init__(self,gateway=None): self.gateway=gateway
    async def submit(self,request:PriorAuthorizationRequest)->PriorAuthorizationResult:
        if self.gateway is None: return PriorAuthorizationResult(status="requires_human_or_payer_workflow")
        return await self.gateway.submit(request)
