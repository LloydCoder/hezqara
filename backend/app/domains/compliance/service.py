class ComplianceService:
    def __init__(self,audit_repository): self.audit_repository=audit_repository
    async def evidence(self,tenant_id:str): return await self.audit_repository.list_for_tenant(tenant_id)
