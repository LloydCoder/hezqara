-- E7: first-clinic production vertical slice activation, evidence and recovery state.
CREATE TABLE IF NOT EXISTS clinic_activation (
  clinic_id text PRIMARY KEY REFERENCES clinics(id) ON DELETE CASCADE,
  state text NOT NULL DEFAULT 'draft' CHECK (state IN ('draft','testing','ready','active','paused','disabled','recovering','recovered')),
  previous_state text,
  activation_version integer NOT NULL DEFAULT 1 CHECK (activation_version >= 1),
  activated_at timestamptz,
  paused_at timestamptz,
  disabled_at timestamptz,
  last_tested_at timestamptz,
  last_recovered_at timestamptz,
  updated_by text,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS activation_evidence (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id text NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
  check_code text NOT NULL,
  status text NOT NULL CHECK (status IN ('passed','failed','skipped')),
  detail jsonb NOT NULL DEFAULT '{}'::jsonb,
  actor_id text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS roi_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id text NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
  period_start date NOT NULL,
  period_end date NOT NULL,
  workflow_runs bigint NOT NULL DEFAULT 0,
  completed_workflows bigint NOT NULL DEFAULT 0,
  communications bigint NOT NULL DEFAULT 0,
  estimated_minutes_saved numeric(14,2) NOT NULL DEFAULT 0,
  estimated_value numeric(14,2) NOT NULL DEFAULT 0,
  methodology jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (period_end >= period_start)
);

CREATE TABLE IF NOT EXISTS tenant_export_manifests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id text NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
  export_type text NOT NULL CHECK (export_type IN ('operational','compliance','recovery')),
  status text NOT NULL DEFAULT 'created' CHECK (status IN ('created','ready','expired','failed')),
  record_counts jsonb NOT NULL DEFAULT '{}'::jsonb,
  checksum text,
  created_by text NOT NULL,
  expires_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['clinic_activation','activation_evidence','roi_snapshots','tenant_export_manifests'] LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',t);
    EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY',t);
    EXECUTE format('REVOKE ALL ON public.%I FROM anon',t);
    EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON public.%I TO authenticated',t);
    EXECUTE format(
      'DROP POLICY IF EXISTS e7_tenant_boundary ON public.%I;
       DROP POLICY IF EXISTS e7_tenant_access ON public.%I;
       CREATE POLICY e7_tenant_boundary ON public.%I AS RESTRICTIVE FOR ALL TO authenticated
       USING (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))
       WITH CHECK (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))',
      t,t,t
    );
    EXECUTE format(
      'CREATE POLICY e7_tenant_access ON public.%I AS PERMISSIVE FOR ALL TO authenticated
       USING (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))
       WITH CHECK (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))',
      t
    );
  END LOOP;
END $$;

CREATE INDEX IF NOT EXISTS activation_evidence_tenant_time ON activation_evidence(clinic_id,created_at DESC);
CREATE INDEX IF NOT EXISTS roi_snapshots_tenant_time ON roi_snapshots(clinic_id,created_at DESC);
CREATE INDEX IF NOT EXISTS tenant_export_manifests_tenant_time ON tenant_export_manifests(clinic_id,created_at DESC);
