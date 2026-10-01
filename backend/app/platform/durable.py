from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy import text

class DurableJobService:
    def __init__(self, session): self.session=session

    async def clinic_id(self, organization_id: str) -> str:
        value=await self.session.scalar(text("select id from clinics where clerk_org_id=:org"),{"org":organization_id})
        if not value: raise ValueError("organization clinic is not provisioned")
        return str(value)

    async def enqueue(self, organization_id: str, job_type: str, idempotency_key: str, payload: dict, request_id: str|None=None, max_attempts: int=5) -> dict:
        clinic=await self.clinic_id(organization_id)
        result=await self.session.execute(text("""
          insert into platform_jobs(clinic_id,job_type,idempotency_key,status,max_attempts,payload,request_id,available_at)
          values(:clinic,:job_type,:key,'queued',:max_attempts,cast(:payload as jsonb),:request_id,now())
          on conflict(clinic_id,idempotency_key) do update
            set updated_at=platform_jobs.updated_at
          returning id,clinic_id,job_type,idempotency_key,status,attempts,max_attempts,available_at,lease_owner,lease_expires_at
        """),{"clinic":clinic,"job_type":job_type,"key":idempotency_key,"max_attempts":max_attempts,"payload":json.dumps(payload),"request_id":request_id})
        return dict(result.mappings().one())

    async def claim(self, job_id: str, worker_id: str, lease_seconds: int=120) -> dict|None:
        result=await self.session.execute(text("""
          update platform_jobs
          set status='running',attempts=attempts+1,last_started_at=now(),
              lease_owner=:worker,lease_expires_at=now()+make_interval(secs=>:lease),
              updated_at=now()
          where id=:id and status in ('queued','failed')
            and available_at<=now()
            and attempts<max_attempts
          returning *
        """),{"id":job_id,"worker":worker_id,"lease":lease_seconds})
        row=result.mappings().first()
        return dict(row) if row else None

    async def claim_due(self, worker_id: str, limit: int=20, lease_seconds: int=120) -> list[dict]:
        result=await self.session.execute(text("""
          with candidates as (
            select id from platform_jobs
            where status in ('queued','failed') and available_at<=now() and attempts<max_attempts
            order by available_at,created_at,id
            for update skip locked
            limit :limit
          )
          update platform_jobs j
          set status='running',attempts=j.attempts+1,last_started_at=now(),
              lease_owner=:worker,lease_expires_at=now()+make_interval(secs=>:lease),updated_at=now()
          from candidates c
          where j.id=c.id
          returning j.*
        """),{"limit":limit,"worker":worker_id,"lease":lease_seconds})
        return [dict(r) for r in result.mappings().all()]

    async def heartbeat(self, job_id: str, worker_id: str, lease_seconds: int=120) -> bool:
        result=await self.session.execute(text("""
          update platform_jobs set lease_expires_at=now()+make_interval(secs=>:lease),updated_at=now()
          where id=:id and status='running' and lease_owner=:worker
        """),{"id":job_id,"worker":worker_id,"lease":lease_seconds})
        return result.rowcount==1

    async def complete(self, job_id: str, worker_id: str, result: dict|None=None) -> bool:
        r=await self.session.execute(text("""
          update platform_jobs set status='completed',result=cast(:result as jsonb),
            lease_owner=NULL,lease_expires_at=NULL,updated_at=now(),completed_at=now()
          where id=:id and status='running' and lease_owner=:worker
        """),{"id":job_id,"worker":worker_id,"result":json.dumps(result or {})})
        return r.rowcount==1

    async def fail(self, job_id: str, worker_id: str, error: str, retryable: bool=True) -> dict|None:
        r=await self.session.execute(text("""
          update platform_jobs
          set status=case when :retryable and attempts<max_attempts then 'failed' else 'dead_letter' end,
              last_error=:error,
              available_at=case when :retryable and attempts<max_attempts
                then now()+make_interval(secs=>least(3600,power(2,greatest(attempts,1))::int))
                else available_at end,
              dead_lettered_at=case when :retryable and attempts<max_attempts then NULL else now() end,
              lease_owner=NULL,lease_expires_at=NULL,updated_at=now()
          where id=:id and status='running' and lease_owner=:worker
          returning id,status,attempts,max_attempts,available_at,last_error
        """),{"id":job_id,"worker":worker_id,"error":error[:1000],"retryable":retryable})
        row=r.mappings().first()
        return dict(row) if row else None

    async def replay(self, job_id: str, request_id: str|None=None) -> dict|None:
        r=await self.session.execute(text("""
          update platform_jobs set status='queued',attempts=0,last_error=NULL,
            dead_lettered_at=NULL,lease_owner=NULL,lease_expires_at=NULL,
            available_at=now(),request_id=coalesce(:request_id,request_id),updated_at=now()
          where id=:id and status='dead_letter'
          returning id,status,attempts,max_attempts,available_at
        """),{"id":job_id,"request_id":request_id})
        row=r.mappings().first()
        return dict(row) if row else None
