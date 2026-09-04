class AnalyticsService:
    def __init__(self,repository): self.repository=repository
    async def summary(self,tenant_id:str): return await self.repository.summary(tenant_id)
