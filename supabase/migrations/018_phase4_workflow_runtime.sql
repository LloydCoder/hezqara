-- Phase 4: durable, tenant-scoped workflow definitions, immutable versions, runs, step runs, approvals and events.
CREATE TABLE IF NOT EXISTS workflows (
  id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
  key TEXT NOT NULL,
  name TEXT NOT NULL CHECK (length(trim(name)) BETWEEN 1 AND 200),
  description TEXT,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','active','paused','archived')),
  created_by TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (clinic_id,key)
);
CREATE TABLE IF NOT EXISTS workflow_versions (
  id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  workflow_id TEXT NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  version INTEGER NOT NULL CHECK (version > 0),
  definition JSONB NOT NULL,
  activated_at TIMESTAMPTZ,
  created_by TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(workflow_id,version)
);
CREATE TABLE IF NOT EXISTS workflow_runs (
  id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
  workflow_id TEXT NOT NULL REFERENCES workflows(id) ON DELETE RESTRICT,
  workflow_version_id TEXT NOT NULL REFERENCES workflow_versions(id) ON DELETE RESTRICT,
  status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','running','waiting_for_approval','completed','failed','escalated','cancelled')),
  trigger_type TEXT NOT NULL,
  trigger_key TEXT,
  actor_id TEXT,
  request_id TEXT,
  idempotency_key TEXT NOT NULL,
  context JSONB NOT NULL DEFAULT '{}'::jsonb,
  result JSONB,
  failure_class TEXT,
  retry_count INTEGER NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(clinic_id,workflow_id,idempotency_key)
);
CREATE TABLE IF NOT EXISTS workflow_step_runs (
  id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  workflow_run_id TEXT NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
  step_key TEXT NOT NULL,
  ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
  status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','running','waiting_for_approval','completed','failed','escalated','cancelled')),
  input JSONB,
  output JSONB,
  error_class TEXT,
  attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(workflow_run_id,step_key)
);
CREATE TABLE IF NOT EXISTS workflow_approvals (
  id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
  workflow_run_id TEXT NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
  workflow_step_run_id TEXT REFERENCES workflow_step_runs(id) ON DELETE CASCADE,
  requested_action JSONB NOT NULL,
  risk_level TEXT NOT NULL CHECK (risk_level IN ('READ','LOW_RISK_WRITE','HIGH_RISK_WRITE','EXTERNAL_SIDE_EFFECT')),
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected','expired','cancelled')),
  requested_by TEXT NOT NULL,
  decided_by TEXT,
  expires_at TIMESTAMPTZ,
  decided_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS workflow_events (
  id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
  workflow_run_id TEXT REFERENCES workflow_runs(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  actor_id TEXT,
  request_id TEXT,
  aggregate_type TEXT,
  aggregate_id TEXT,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_workflows_clinic_status ON workflows(clinic_id,status,updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_versions_workflow ON workflow_versions(workflow_id,version DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_clinic_status ON workflow_runs(clinic_id,status,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_request ON workflow_runs(clinic_id,request_id) WHERE request_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_workflow_step_runs_run ON workflow_step_runs(workflow_run_id,ordinal);
CREATE INDEX IF NOT EXISTS idx_workflow_approvals_clinic_status ON workflow_approvals(clinic_id,status,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflow_events_clinic_created ON workflow_events(clinic_id,created_at DESC);
DO $$ DECLARE t text; BEGIN FOREACH t IN ARRAY ARRAY['workflows','workflow_versions','workflow_runs','workflow_step_runs','workflow_approvals','workflow_events'] LOOP EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',t); EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY',t); EXECUTE format('DROP POLICY IF EXISTS hezqara_tenant_select ON public.%I',t); EXECUTE format('DROP POLICY IF EXISTS hezqara_tenant_insert ON public.%I',t); EXECUTE format('CREATE POLICY hezqara_tenant_select ON public.%I FOR SELECT TO authenticated USING (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))',t); EXECUTE format('CREATE POLICY hezqara_tenant_insert ON public.%I FOR INSERT TO authenticated WITH CHECK (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))',t); EXECUTE format('CREATE POLICY hezqara_tenant_update ON public.%I FOR UPDATE TO authenticated USING (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true))) WITH CHECK (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))',t); EXECUTE format('GRANT SELECT,INSERT,UPDATE ON public.%I TO authenticated',t); END LOOP; END $$;
CREATE OR REPLACE FUNCTION public.reject_workflow_history_mutation() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN RAISE EXCEPTION 'workflow history is immutable'; END;$$;
DROP TRIGGER IF EXISTS workflow_version_immutable ON public.workflow_versions; CREATE TRIGGER workflow_version_immutable BEFORE UPDATE OR DELETE ON public.workflow_versions FOR EACH ROW EXECUTE FUNCTION public.reject_workflow_history_mutation();
DROP TRIGGER IF EXISTS workflow_event_immutable ON public.workflow_events; CREATE TRIGGER workflow_event_immutable BEFORE UPDATE OR DELETE ON public.workflow_events FOR EACH ROW EXECUTE FUNCTION public.reject_workflow_history_mutation();
