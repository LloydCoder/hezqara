from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import text

DEFAULT_SLOS = (
    {"name":"api_availability","target":0.999,"metric":"availability","window_days":30},
    {"name":"durable_job_success","target":0.995,"metric":"job_success","window_days":30},
)

async def _clinic_id(session, organization_id: str) -> str:
    clinic = await session.scalar(text("select id from clinics where clerk_org_id=:org"), {"org": organization_id})
    if not clinic:
        raise ValueError("organization clinic is not provisioned")
    return str(clinic)

async def readiness(session) -> dict:
    checks = {}
    try:
        await session.execute(text("select 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"
    try:
        await session.execute(text("select count(*) from platform_jobs"))
        checks["durable_jobs"] = "ok"
    except Exception:
        checks["durable_jobs"] = "unavailable"
    worker = (await session.execute(text("select public.healthy_worker_count(interval '2 minutes')"))).scalar_one()
    checks["worker_heartbeat"] = "ok" if worker > 0 else "degraded"
    return {"status":"ready" if all(v=="ok" for v in checks.values()) else "degraded","checks":checks,"generated_at":datetime.now(timezone.utc)}

async def operational_snapshot(session, organization_id: str) -> dict:
    clinic = await _clinic_id(session, organization_id)
    incidents = (await session.execute(text("select count(*) from operational_incidents where clinic_id=:clinic and status not in ('resolved','closed')"),{"clinic":clinic})).scalar_one()
    jobs = (await session.execute(text("select count(*) from platform_jobs where clinic_id=:clinic and status in ('queued','running','failed')"),{"clinic":clinic})).scalar_one()
    workers = (await session.execute(text("select public.healthy_worker_count(interval '2 minutes')"))).scalar_one()
    return {"clinic_id":clinic,"open_incidents":incidents,"active_or_retrying_jobs":jobs,"healthy_workers":workers,"generated_at":datetime.now(timezone.utc)}

async def record_worker_heartbeat(session, worker_id: str, queue: str, active_jobs: int = 0, version: str|None = None) -> None:
    await session.execute(text("""
      insert into worker_heartbeats(worker_id,queue,active_jobs,version,last_seen_at)
      values(:id,:queue,:active,:version,now())
      on conflict(worker_id) do update set queue=excluded.queue,active_jobs=excluded.active_jobs,
      version=excluded.version,last_seen_at=now()
    """),{"id":worker_id,"queue":queue,"active":active_jobs,"version":version})
