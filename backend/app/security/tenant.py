from dataclasses import dataclass
from fastapi import HTTPException

@dataclass(frozen=True)
class TenantContext:
    organization_id: str
    user_id: str
    permissions: frozenset[str]
    role: str | None = None

    def require(self, permission: str) -> None:
        if permission not in self.permissions:
            raise HTTPException(status_code=403, detail="insufficient permissions")
