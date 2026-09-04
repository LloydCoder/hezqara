from app.domains.insurance.schemas import EligibilityRequest,EligibilityResult
class InsuranceService:
    def __init__(self,gateway=None): self.gateway=gateway
    async def verify(self,request:EligibilityRequest)->EligibilityResult:
        if self.gateway is None: return EligibilityResult(status="requires_external_verification",payer_id=request.payer_id,patient_id=request.patient_id,source="not_configured")
        return await self.gateway.verify(request)
