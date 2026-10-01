# E3 Durable Execution & Distributed Reliability — VERIFIED

## Scope

E3 makes durable execution state authoritative in PostgreSQL. Redis/Celery is a delivery and wake-up mechanism, not the source of truth.

## Controls

- Durable platform job state with queued/running/completed/failed/cancelled/dead_letter lifecycle.
- Persistent idempotency keys for jobs and workflow steps.
- Atomic worker claiming with row locking and SKIP LOCKED for due jobs.
- Worker leases with expiry and heartbeats.
- Bounded attempts and exponential retry backoff.
- Dead-letter state after exhaustion.
- Explicit replay of dead-lettered jobs.
- Expired job/workflow/outbox leases are reconciled by a privileged internal recovery function.
- Workflow execution itself carries a lease, preventing concurrent workers from progressing the same run.
- Approval pauses release workflow leases; approval resumes execution through the durable job path.
- Celery uses late acknowledgements and rejects tasks on worker loss so broker delivery does not falsely imply durable completion.
- Periodic dispatch and lease reconciliation run through the single Celery Beat service.

The design follows established durable-execution principles: persist state separately from broker delivery, make operations idempotent, bound retries, and recover abandoned work. Celery's late-ack/worker-loss controls complement rather than replace database durability. citeturn4search7turn5search0

## Adversarial proof

The E3 validation suite verifies duplicate worker claims are rejected, expired leases recover, exhausted jobs become dead-lettered, tenant RLS remains enforced, workflow execution survives approval pause/resume, and the complete application vertical slice remains green.

## Verification

E3 is VERIFIED. This is an engineering reliability status, not a claim of production scale, RPO/RTO certification, or operational maturity.
