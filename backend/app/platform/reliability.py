from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import text

logger = logging.getLogger(__name__)

DEFAULT_SLOS = (
    {"name": "api_availability", "target": 0.999, "metric": "availability", "window_days": 30},
    {"name": "durable_job_success", "target": 0.995, "metric": "job_success", "window_days": 30},
)


def _safe_database_error_context(exc: Exception) -> tuple[str, str, bool]:
    """Return allow-listed DB failure metadata; never return exception text or connection details."""
    original = getattr(exc, "orig", None)
    sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
    if not isinstance(sqlstate, str) or len(sqlstate) != 5 or not sqlstate.isalnum():
        sqlstate = "unknown"
    original_type = type(original).__name__ if original is not None else type(exc).__name__
    # Exception class names are runtime identifiers; never include str(exc), repr(exc), DSNs or parameters.
    return original_type, sqlstate, bool(getattr(exc, "connection_invalidated", False))


def _log_readiness_failure(check_name: str, exc: Exception) -> None:
    original_type, sqlstate, connection_invalidated = _safe_database_error_context(exc)
    logger.warning(
        "Readiness %s check failed (exception=%s sqlstate=%s connection_invalidated=%s)",
        check_name,
        original_type,
        sqlstate,
        connection_invalidated,
    )


async def _clinic_id(session, organization_id: str) -> str:
    clinic = await session.scalar(text("select id from clinics where clerk_org_id=:org"), {"org": organization_id})
    if not clinic:
        raise ValueError("organization clinic is not provisioned")
    return str(clinic)


async def readiness(session) -> dict:
    """Check readiness dependencies independently; log safe failure categories only."""
    checks = {}
    try:
        await session.execute(text("select 1"))
        checks["database"] = "ok"
    except Exception as exc:
        _log_readiness_failure("database connectivity", exc)
        checks["database"] = "unavailable"

    try:
        await session.execute(text("select count(*) from platform_jobs"))
        checks["durable_jobs"] = "ok"
    except Exception as exc:
        _log_readiness_failure("durable-job schema", exc)
        checks["durable_jobs"] = "unavailable"

    try:
        worker = (
            await session.execute(
                text("select public.healthy_worker_count(interval '2 minutes')")
            )
        ).scalar_one()
        checks["worker_heartbeat"] = "ok" if worker > 0 else "degraded"
    except Exception as exc:
        _log_readiness_failure("worker-heartbeat", exc)
        checks["worker_heartbeat"] = "unavailable"

    return {
        "status": "ready" if all(value == "ok" for value in checks.values()) else "degraded",
        "checks": checks,
        "generated_at": datetime.now(timezone.utc),
    }


async def operational_snapshot(session, organization_id: str) -> dict:
    clinic = await _clinic_id(session, organization_id)
    incidents = (await session.execute(text("select count(*) from operational_incidents where clinic_id=:clinic and status not in ('resolved','closed')"), {"clinic": clinic})).scalar_one()
    jobs = (await session.execute(text("select count(*) from platform_jobs where clinic_id=:clinic and status in ('queued','running','failed')"), {"clinic": clinic})).scalar_one()
    workers = (await session.execute(text("select public.healthy_worker_count(interval '2 minutes')"))).scalar_one()
    return {"clinic_id": clinic, "open_incidents": incidents, "active_or_retrying_jobs": jobs, "healthy_workers": workers, "generated_at": datetime.now(timezone.utc)}


async def record_worker_heartbeat(session, worker_id: str, queue: str, active_jobs: int = 0, version: str | None = None) -> None:
    await session.execute(text("""
      insert into worker_heartbeats(worker_id,queue,active_jobs,version,last_seen_at)
      values(:id,:queue,:active,:version,now())
      on conflict(worker_id) do update set queue=excluded.queue,active_jobs=excluded.active_jobs,
      version=excluded.version,last_seen_at=now()
    """), {"id": worker_id, "queue": queue, "active": active_jobs, "version": version})
