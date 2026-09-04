from fastapi import Depends
from app.security.clerk import current_tenant
from app.security.tenant import TenantContext

def require_permission(permission: str):
    async def dependency(tenant: TenantContext = Depends(current_tenant)) -> TenantContext:
        tenant.require(permission)
        return tenant
    return dependency
