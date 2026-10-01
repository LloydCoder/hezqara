-- E3: durable execution state, leases, bounded retries and replay.
ALTER TABLE public.platform_jobs
  DROP CONSTRAINT IF EXISTS platform_jobs_status_check;
ALTER TABLE public.platform_jobs
  ADD CONSTRAINT platform_jobs_status_check CHECK (status IN ('queued','running','completed','failed','cancelled','dead_letter'));

ALTER TABLE public.platform_jobs
  ADD COLUMN IF NOT EXISTS max_attempts integer NOT NULL DEFAULT 5 CHECK (max_attempts BETWEEN 1 AND 20),
  ADD COLUMN IF NOT EXISTS lease_owner text,
  ADD COLUMN IF NOT EXISTS lease_expires_at timestamptz,
  ADD COLUMN IF NOT EXISTS last_started_at timestamptz,
  ADD COLUMN IF NOT EXISTS result jsonb,
  ADD COLUMN IF NOT EXISTS request_id text,
  ADD COLUMN IF NOT EXISTS dead_lettered_at timestamptz;

CREATE INDEX IF NOT EXISTS platform_jobs_due_idx
  ON public.platform_jobs(status,available_at)
  WHERE status IN ('queued','failed');
CREATE INDEX IF NOT EXISTS platform_jobs_lease_idx
  ON public.platform_jobs(lease_expires_at)
  WHERE status='running';

ALTER TABLE public.workflow_runs
  ADD COLUMN IF NOT EXISTS attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
  ADD COLUMN IF NOT EXISTS max_attempts integer NOT NULL DEFAULT 5 CHECK (max_attempts BETWEEN 1 AND 20),
  ADD COLUMN IF NOT EXISTS next_attempt_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS lease_owner text,
  ADD COLUMN IF NOT EXISTS lease_expires_at timestamptz,
  ADD COLUMN IF NOT EXISTS heartbeat_at timestamptz;

ALTER TABLE public.workflow_step_runs
  ADD COLUMN IF NOT EXISTS idempotency_key text,
  ADD COLUMN IF NOT EXISTS lease_owner text,
  ADD COLUMN IF NOT EXISTS lease_expires_at timestamptz,
  ADD COLUMN IF NOT EXISTS heartbeat_at timestamptz;

UPDATE public.workflow_step_runs
SET idempotency_key=workflow_run_id||':'||step_key
WHERE idempotency_key IS NULL;

CREATE OR REPLACE FUNCTION public.workflow_step_runs_set_idempotency()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $
BEGIN
  NEW.idempotency_key := COALESCE(NEW.idempotency_key, NEW.workflow_run_id || ':' || NEW.step_key);
  RETURN NEW;
END $;
REVOKE ALL ON FUNCTION public.workflow_step_runs_set_idempotency() FROM PUBLIC;

DROP TRIGGER IF EXISTS workflow_step_runs_idempotency_before_insert ON public.workflow_step_runs;
CREATE TRIGGER workflow_step_runs_idempotency_before_insert
BEFORE INSERT ON public.workflow_step_runs
FOR EACH ROW EXECUTE FUNCTION public.workflow_step_runs_set_idempotency();

ALTER TABLE public.workflow_step_runs ALTER COLUMN idempotency_key SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS workflow_step_runs_idempotency_idx
  ON public.workflow_step_runs(clinic_id,idempotency_key);

ALTER TABLE public.outbox_events
  ADD COLUMN IF NOT EXISTS max_attempts integer NOT NULL DEFAULT 5 CHECK (max_attempts BETWEEN 1 AND 20),
  ADD COLUMN IF NOT EXISTS lease_owner text,
  ADD COLUMN IF NOT EXISTS lease_expires_at timestamptz,
  ADD COLUMN IF NOT EXISTS heartbeat_at timestamptz,
  ADD COLUMN IF NOT EXISTS dead_lettered_at timestamptz;

ALTER TABLE public.outbox_events
  DROP CONSTRAINT IF EXISTS outbox_events_status_check;
ALTER TABLE public.outbox_events
  ADD CONSTRAINT outbox_events_status_check CHECK (status IN ('pending','processing','published','failed','dead_letter'));

CREATE INDEX IF NOT EXISTS outbox_events_lease_idx
  ON public.outbox_events(lease_expires_at)
  WHERE status='processing';

-- Recover jobs/workflow steps abandoned by a crashed worker. Backoff is bounded
-- and deterministic; the worker remains responsible for actual execution.
CREATE OR REPLACE FUNCTION public.recover_expired_execution_leases(p_now timestamptz DEFAULT now())
RETURNS TABLE(platform_jobs_recovered bigint, workflow_runs_recovered bigint, workflow_steps_recovered bigint, outbox_events_recovered bigint)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  j bigint; w bigint; s bigint; o bigint;
BEGIN
  UPDATE public.platform_jobs
  SET status=CASE WHEN attempts >= max_attempts THEN 'dead_letter' ELSE 'failed' END,
      available_at=CASE WHEN attempts >= max_attempts THEN available_at ELSE p_now + make_interval(secs=>LEAST(3600,POWER(2,GREATEST(attempts,1))::int)) END,
      lease_owner=NULL,lease_expires_at=NULL,dead_lettered_at=CASE WHEN attempts >= max_attempts THEN p_now ELSE dead_lettered_at END,updated_at=p_now
  WHERE status='running' AND lease_expires_at IS NOT NULL AND lease_expires_at < p_now;
  GET DIAGNOSTICS j=ROW_COUNT;

  UPDATE public.workflow_step_runs
  SET status='queued',lease_owner=NULL,lease_expires_at=NULL,heartbeat_at=NULL,
      error_class='WORKER_LEASE_EXPIRED'
  WHERE status='running' AND lease_expires_at IS NOT NULL AND lease_expires_at < p_now;
  GET DIAGNOSTICS s=ROW_COUNT;

  UPDATE public.workflow_runs
  SET status='queued',next_attempt_at=p_now,lease_owner=NULL,lease_expires_at=NULL,heartbeat_at=NULL,
      retry_count=retry_count+1,attempt_count=attempt_count+1,failure_class='WORKER_LEASE_EXPIRED',updated_at=p_now
  WHERE status='running' AND lease_expires_at IS NOT NULL AND lease_expires_at < p_now
    AND attempt_count < max_attempts;
  GET DIAGNOSTICS w=ROW_COUNT;

  UPDATE public.workflow_runs
  SET status='failed',lease_owner=NULL,lease_expires_at=NULL,heartbeat_at=NULL,
      retry_count=retry_count+1,attempt_count=attempt_count+1,failure_class='WORKER_LEASE_EXPIRED',updated_at=p_now
  WHERE status='running' AND lease_expires_at IS NOT NULL AND lease_expires_at < p_now
    AND attempt_count >= max_attempts;

  UPDATE public.outbox_events
  SET status=CASE WHEN attempts >= max_attempts THEN 'dead_letter' ELSE 'pending' END,
      available_at=CASE WHEN attempts >= max_attempts THEN available_at ELSE p_now + make_interval(secs=>LEAST(3600,POWER(2,GREATEST(attempts,1))::int)) END,
      lease_owner=NULL,lease_expires_at=NULL,heartbeat_at=NULL,dead_lettered_at=CASE WHEN attempts >= max_attempts THEN p_now ELSE dead_lettered_at END,updated_at=p_now
  WHERE status='processing' AND lease_expires_at IS NOT NULL AND lease_expires_at < p_now;
  GET DIAGNOSTICS o=ROW_COUNT;

  RETURN QUERY SELECT j,w,s,o;
END $$;
REVOKE ALL ON FUNCTION public.recover_expired_execution_leases(timestamptz) FROM PUBLIC;

COMMENT ON TABLE public.platform_jobs IS 'Durable tenant-scoped job state. Database state is authoritative; broker delivery is only a wake-up mechanism.';
COMMENT ON COLUMN public.workflow_runs.lease_expires_at IS 'Worker lease; expired leases are recoverable by the durable execution reconciler.';
COMMENT ON COLUMN public.outbox_events.lease_expires_at IS 'Dispatcher lease; expired processing is retried or dead-lettered.';
