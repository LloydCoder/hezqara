-- E3 durable execution adversarial verification.
BEGIN;
INSERT INTO clinics(id,name,clerk_org_id) VALUES ('e3-tenant','E3 Tenant','e3_org') ON CONFLICT DO NOTHING;
SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','e3_org',false);

INSERT INTO platform_jobs(clinic_id,job_type,idempotency_key,payload)
VALUES ('e3-tenant','workflow.execute','e3-job','{"organization_id":"e3_org","run_id":"missing"}'::jsonb)
ON CONFLICT (clinic_id,idempotency_key) DO NOTHING;

DO $$
DECLARE job_id uuid; first_status text; second_status text;
BEGIN
  SELECT id INTO job_id FROM platform_jobs WHERE clinic_id='e3-tenant' AND idempotency_key='e3-job';
  UPDATE platform_jobs SET status='running',attempts=attempts+1,lease_owner='worker-a',lease_expires_at=now()+interval '2 minutes' WHERE id=job_id AND status='queued';
  IF NOT FOUND THEN RAISE EXCEPTION 'E3 first worker could not claim job'; END IF;
  UPDATE platform_jobs SET status='running',attempts=attempts+1,lease_owner='worker-b',lease_expires_at=now()+interval '2 minutes' WHERE id=job_id AND status='queued';
  IF FOUND THEN RAISE EXCEPTION 'E3 duplicate worker claim succeeded'; END IF;
END $$;

UPDATE platform_jobs SET lease_expires_at=now()-interval '1 second' WHERE clinic_id='e3-tenant' AND idempotency_key='e3-job';
RESET ROLE;
SELECT * FROM public.recover_expired_execution_leases(now());
SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','e3_org',false);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM platform_jobs WHERE clinic_id='e3-tenant' AND idempotency_key='e3-job' AND status='failed' AND lease_owner IS NULL) THEN
    RAISE EXCEPTION 'E3 expired job was not recovered';
  END IF;
END $$;

UPDATE platform_jobs SET status='running',attempts=max_attempts,lease_owner='worker-dead',lease_expires_at=now()-interval '1 second' WHERE clinic_id='e3-tenant' AND idempotency_key='e3-job';
RESET ROLE;
SELECT * FROM public.recover_expired_execution_leases(now());
SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','e3_org',false);
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM platform_jobs WHERE clinic_id='e3-tenant' AND idempotency_key='e3-job' AND status='dead_letter') THEN
    RAISE EXCEPTION 'E3 exhausted job was not dead-lettered';
  END IF;
END $$;

DO $$
BEGIN
  INSERT INTO workflow_step_runs(id,clinic_id,workflow_run_id,step_key,ordinal,idempotency_key)
  VALUES ('e3-step-a','e3-tenant','missing-run','step-a',0,'e3-step-key');
EXCEPTION WHEN foreign_key_violation THEN NULL;
END $$;

RESET ROLE;
ROLLBACK;
