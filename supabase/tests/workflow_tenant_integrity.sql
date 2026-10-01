-- Database-level tenant integrity proof for workflow relationships.
-- RLS is intentionally active: each forged write uses the attacker's own
-- tenant row so a successful RLS check reaches the composite FK boundary.
BEGIN;

INSERT INTO clinics(id,name,clerk_org_id) VALUES
  ('ci-wf-tenant-a','CI Workflow Tenant A','ci_wf_org_a'),
  ('ci-wf-tenant-b','CI Workflow Tenant B','ci_wf_org_b')
ON CONFLICT (id) DO NOTHING;

SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','ci_wf_org_a',false);

INSERT INTO workflows(id,clinic_id,key,name,created_by)
VALUES ('ci-wf-a','ci-wf-tenant-a','ci-wf','Tenant A workflow','ci-user-a')
ON CONFLICT (id) DO NOTHING;

INSERT INTO workflow_versions(id,clinic_id,workflow_id,version,definition,created_by)
VALUES ('ci-wfv-a','ci-wf-tenant-a','ci-wf-a',1,'{"steps":[]}'::jsonb,'ci-user-a')
ON CONFLICT (id) DO NOTHING;

INSERT INTO workflow_runs(id,clinic_id,workflow_id,workflow_version_id,trigger_type,actor_id,idempotency_key)
VALUES ('ci-wfr-a','ci-wf-tenant-a','ci-wf-a','ci-wfv-a','test','ci-user-a','ci-wfr-a')
ON CONFLICT (id) DO NOTHING;

INSERT INTO workflow_step_runs(id,clinic_id,workflow_run_id,step_key,ordinal)
VALUES ('ci-wfs-a','ci-wf-tenant-a','ci-wfr-a','step-a',0)
ON CONFLICT (id) DO NOTHING;

SELECT set_config('app.clerk_org_id','ci_wf_org_b',false);

INSERT INTO workflows(id,clinic_id,key,name,created_by)
VALUES ('ci-wf-b','ci-wf-tenant-b','ci-wf','Tenant B workflow','ci-user-b')
ON CONFLICT (id) DO NOTHING;

INSERT INTO workflow_versions(id,clinic_id,workflow_id,version,definition,created_by)
VALUES ('ci-wfv-b','ci-wf-tenant-b','ci-wf-b',1,'{"steps":[]}'::jsonb,'ci-user-b')
ON CONFLICT (id) DO NOTHING;

INSERT INTO workflow_runs(id,clinic_id,workflow_id,workflow_version_id,trigger_type,actor_id,idempotency_key)
VALUES ('ci-wfr-b','ci-wf-tenant-b','ci-wf-b','ci-wfv-b','test','ci-user-b','ci-wfr-b')
ON CONFLICT (id) DO NOTHING;

-- A tenant-B actor can satisfy RLS with tenant-B clinic_id, but cannot bind
-- the run to tenant-A workflow/version identifiers.
DO $$
BEGIN
  BEGIN
    INSERT INTO workflow_runs(id,clinic_id,workflow_id,workflow_version_id,trigger_type,actor_id,idempotency_key)
    VALUES ('ci-wfr-forged-workflow','ci-wf-tenant-b','ci-wf-a','ci-wfv-b','test','ci-user-b','ci-wfr-forged-workflow');
    RAISE EXCEPTION 'cross-tenant workflow FK unexpectedly succeeded';
  EXCEPTION WHEN foreign_key_violation OR check_violation OR insufficient_privilege THEN NULL;
  END;
END $$;

DO $$
BEGIN
  BEGIN
    INSERT INTO workflow_runs(id,clinic_id,workflow_id,workflow_version_id,trigger_type,actor_id,idempotency_key)
    VALUES ('ci-wfr-forged-version','ci-wf-tenant-b','ci-wf-b','ci-wfv-a','test','ci-user-b','ci-wfr-forged-version');
    RAISE EXCEPTION 'cross-tenant workflow version FK unexpectedly succeeded';
  EXCEPTION WHEN foreign_key_violation OR check_violation OR insufficient_privilege THEN NULL;
  END;
END $$;

DO $$
BEGIN
  BEGIN
    INSERT INTO workflow_step_runs(id,clinic_id,workflow_run_id,step_key,ordinal)
    VALUES ('ci-wfs-forged','ci-wf-tenant-a','ci-wfr-b','forged',0);
    RAISE EXCEPTION 'cross-tenant workflow step FK unexpectedly succeeded';
  EXCEPTION WHEN foreign_key_violation OR check_violation OR insufficient_privilege THEN NULL;
  END;
END $$;

DO $$
BEGIN
  BEGIN
    INSERT INTO workflow_approvals(id,clinic_id,workflow_run_id,requested_action,risk_level,requested_by)
    VALUES ('ci-wfa-forged-run','ci-wf-tenant-b','ci-wfr-a','{"action":"test"}'::jsonb,'READ','ci-user-b');
    RAISE EXCEPTION 'cross-tenant approval/run FK unexpectedly succeeded';
  EXCEPTION WHEN foreign_key_violation OR check_violation OR insufficient_privilege THEN NULL;
  END;
END $$;

DO $$
BEGIN
  BEGIN
    INSERT INTO workflow_approvals(id,clinic_id,workflow_run_id,workflow_step_run_id,requested_action,risk_level,requested_by)
    VALUES ('ci-wfa-forged-step','ci-wf-tenant-b','ci-wfr-b','ci-wfs-a','{"action":"test"}'::jsonb,'READ','ci-user-b');
    RAISE EXCEPTION 'cross-tenant approval/step FK unexpectedly succeeded';
  EXCEPTION WHEN foreign_key_violation OR check_violation OR insufficient_privilege THEN NULL;
  END;
END $$;

DO $$
BEGIN
  BEGIN
    INSERT INTO workflow_events(id,clinic_id,workflow_run_id,event_type,payload)
    VALUES ('ci-wfe-forged','ci-wf-tenant-b','ci-wfr-a','test','{}'::jsonb);
    RAISE EXCEPTION 'cross-tenant workflow event FK unexpectedly succeeded';
  EXCEPTION WHEN foreign_key_violation OR check_violation OR insufficient_privilege THEN NULL;
  END;
END $$;

RESET ROLE;
ROLLBACK;
