import logging
from typing import Any

logger = logging.getLogger("hezqara.audit")
_SENSITIVE = {"authorization", "token", "password", "secret", "api_key", "access_token", "refresh_token"}

def sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    clean = {}
    for key, value in (metadata or {}).items():
        if any(part in key.lower() for part in _SENSITIVE):
            continue
        clean[key] = value if isinstance(value, (str, int, float, bool, type(None))) else str(value)[:500]
    return clean

def record(*, tenant: str, actor: str, action: str, resource: str, resource_id: str | None, outcome: str, request_id: str | None = None, metadata: dict[str, Any] | None = None) -> None:
    logger.info("audit actor=%s tenant=%s action=%s resource=%s resource_id=%s outcome=%s request_id=%s metadata=%s", actor, tenant, action, resource, resource_id, outcome, request_id, sanitize_metadata(metadata))
