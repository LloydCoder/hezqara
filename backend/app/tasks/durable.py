import asyncio
import os
from app.tasks.celery import celery_app
from app.infrastructure.database import system_session_context
from app.platform.durable import DurableJobService
from app.domains.workflows.runtime import execute_run
from app.domains.patient_engagement.outbox import process_communication_outbox

_worker_loop = None
_worker_loop_pid = None

def _run_async(coro):
    global _worker_loop, _worker_loop_pid
    pid = os.getpid()
    if _worker_loop is None or _worker_loop.is_closed() or _worker_loop_pid != pid:
        if _worker_loop is not None and not _worker_loop.is_closed():
            _worker_loop.close()
        _worker_loop = asyncio.new_event_loop()
        _worker_loop_pid = pid
    return _worker_loop.run_until_complete(coro)

@celery_app.task(bind=True,acks_late=True,task_reject_on_worker_lost=True,max_retries=0,time_limit=300,soft_time_limit=240)
def run_platform_job(self, job_id: str):
    return _run_async(_run_platform_job(job_id))

async def _run_platform_job(job_id: str):
    worker_id=f"{os.uname().nodename}:{os.getpid()}"
    async with system_session_context() as session:
        jobs=DurableJobService(session)
        job=await jobs.claim(job_id,worker_id)
        if not job:return {"status":"not_claimed","job_id":job_id}
        try:
            payload=job["payload"] or {}
            job_type=job["job_type"]
            if job_type=="workflow.execute":
                result=await execute_run(str(payload["organization_id"]),str(payload["run_id"]))
            elif job_type=="communication.outbox":
                result={"processed":await process_communication_outbox(str(payload["organization_id"]))}
            else:
                raise ValueError(f"unsupported durable job type: {job_type}")
            await jobs.complete(job_id,worker_id,{"result":result})
            return {"status":"completed","job_id":job_id,"result":result}
        except Exception as exc:
            state=await jobs.fail(job_id,worker_id,type(exc).__name__,retryable=True)
            return {"status":state["status"] if state else "lost_lease","job_id":job_id,"error":type(exc).__name__}

@celery_app.task(bind=True,acks_late=True,task_reject_on_worker_lost=True,max_retries=0,time_limit=60)
def dispatch_due_platform_jobs(self, limit: int=20):
    return _run_async(_dispatch_due_platform_jobs(limit))

async def _dispatch_due_platform_jobs(limit:int):
    from sqlalchemy import text
    dispatched=0
    async with system_session_context() as session:
        rows=await session.execute(text("""
          select id from platform_jobs
          where status in ('queued','failed') and available_at<=now() and attempts<max_attempts
          order by available_at,created_at,id limit :limit
        """),{"limit":limit})
        ids=[str(r.id) for r in rows]
    for job_id in ids:
        run_platform_job.delay(job_id)
        dispatched+=1
    return {"dispatched":dispatched}

@celery_app.task(bind=True,acks_late=True,task_reject_on_worker_lost=True,max_retries=0,time_limit=60)
def reconcile_execution_leases(self):
    return _run_async(_reconcile_execution_leases())

async def _reconcile_execution_leases():
    from sqlalchemy import text
    async with system_session_context() as session:
        result=(await session.execute(text("select * from public.recover_expired_execution_leases(now())"))).mappings().one()
        return dict(result)
