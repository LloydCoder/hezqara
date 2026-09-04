class OperationsService:
    def __init__(self,repository): self.repository=repository
    async def queue(self,tenant_id:str): return await self.repository.pending_for_tenant(tenant_id)
