"""Structured audit logging with PHI-safe metadata handling."""
from datetime import UTC, datetime
from typing import Any, Optional

import structlog

logger = structlog.get_logger(__name__)

_SENSITIVE_KEYS = {
    "name", "first_name", "last_name", "full_name", "phone", "email",
    "date_of_birth", "dob", "address", "street", "city", "state", "zip",
    "transcript", "message", "content", "notes", "diagnosis", "symptoms",
    "medications", "member_id", "insurance_member_id", "ssn",
}


def _sanitize(value: Any, depth: int = 0) -> Any:
    """Recursively redact likely PHI/secrets from arbitrary metadata."""
    if depth > 4:
        return "[truncated]"
    if isinstance(value, dict):
        return {
            str(k): "[redacted]" if str(k).lower() in _SENSITIVE_KEYS else _sanitize(v, depth + 1)
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_sanitize(v, depth + 1) for v in value[:50]]
    if isinstance(value, str) and len(value) > 500:
        return value[:500] + "…"
    return value


def write_audit_log(
    event_type: str,
    clinic_id: str,
    call_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    action: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    """Emit a PHI-minimized audit event; never log raw request content."""
    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "clinic_id": clinic_id,
        "call_id": call_id,
        "patient_id": patient_id,
        "agent_type": agent_type,
        "action": action,
        "metadata": _sanitize(metadata or {}),
    }
    logger.info("hipaa_audit", **{k: v for k, v in entry.items() if v is not None})
