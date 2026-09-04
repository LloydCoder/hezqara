"""
HIPAA Audit Log Writer.
Every PHI access must be logged. This is non-negotiable.
"""
import structlog
from datetime import datetime, UTC
from typing import Optional

logger = structlog.get_logger(__name__)


def write_audit_log(
    event_type: str,
    clinic_id: str,
    call_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    action: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    """
    Write a HIPAA-compliant audit log entry.

    Every PHI access, every agent action, every call event
    must be recorded here. No raw PHI in the log values.
    """
    log_entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "clinic_id": clinic_id,
        "call_id": call_id,
        "patient_id": patient_id,
        "agent_type": agent_type,
        "action": action,
        "metadata": metadata or {},
    }

    # Remove None values
    log_entry = {k: v for k, v in log_entry.items() if v is not None}

    logger.info("hipaa_audit", **log_entry)
