-- E5: enterprise security, privacy, access review and recovery evidence.
CREATE TABLE IF NOT EXISTS security_incidents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id text NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
  severity text NOT NULL CHECK (severity IN ('low','medium','high','critical')),
  status text NOT NULL DEFAULT 'open' CHECK (status IN ('open','contained','eradicated','recovered','closed')),
  category text NOT NULL,
  summary text NOT NULL,
  detected_at timestamptz NOT NULL DEFAULT now(),
  contained_at timestamptz,
  recovered_at timestamptz,
  closed_at timestamptz,
  owner_id text,
  request_id text,
  evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS security_access_reviews (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id text NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
  subject_id text NOT NULL,
  subject_role text,
  reviewer_id text NOT NULL,
  decision text NOT NULL CHECK (decision IN ('approved','revoked','needs_review')),
  permissions_snapshot jsonb NOT NULL DEFAULT '[]'::jsonb,
  reviewed_at timestamptz NOT NULL DEFAULT now(),
  next_review_at timestamptz,
  evidence jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS privacy_processing_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id text NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
  processor_name text NOT NULL,
  data_category text NOT NULL,
  purpose text NOT NULL,
  processing_region text,
  retention_days integer NOT NULL CHECK (retention_days BETWEEN 1 AND 3650),
  deletion_method text NOT NULL,
  agreement_type text CHECK (agreement_type IN ('baa','dpa','contract','none','not_applicable')),
  agreement_status text NOT NULL DEFAULT 'pending' CHECK (agreement_status IN ('pending','active','expired','not_required')),
  last_reviewed_at timestamptz,
  evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS data_deletion_requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id text NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
  requested_by text NOT NULL,
  scope text NOT NULL,
  status text NOT NULL DEFAULT 'requested' CHECK (status IN ('requested','approved','processing','completed','rejected')),
  requested_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  evidence jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS backup_restore_drills (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id text NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
  backup_reference text NOT NULL,
  started_at timestamptz NOT NULL,
  completed_at timestamptz,
  result text NOT NULL CHECK (result IN ('planned','passed','failed')),
  measured_rpo_seconds integer CHECK (measured_rpo_seconds IS NULL OR measured_rpo_seconds >= 0),
  measured_rto_seconds integer CHECK (measured_rto_seconds IS NULL OR measured_rto_seconds >= 0),
  evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'security_incidents',
    'security_access_reviews',
    'privacy_processing_records',
    'data_deletion_requests',
    'backup_restore_drills'
  ] LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY', t);
    EXECUTE format('REVOKE ALL ON public.%I FROM anon', t);
    EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON public.%I TO authenticated', t);
    EXECUTE format(
      'DROP POLICY IF EXISTS e5_tenant_boundary ON public.%I;
       CREATE POLICY e5_tenant_boundary ON public.%I AS RESTRICTIVE FOR ALL TO authenticated
       USING (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))
       WITH CHECK (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))',
      t, t
    );
  END LOOP;
END $$;

CREATE INDEX IF NOT EXISTS security_incidents_tenant_time ON security_incidents(clinic_id,created_at DESC);
CREATE INDEX IF NOT EXISTS security_access_reviews_due ON security_access_reviews(clinic_id,next_review_at);
CREATE INDEX IF NOT EXISTS privacy_processing_review ON privacy_processing_records(clinic_id,last_reviewed_at);
CREATE INDEX IF NOT EXISTS data_deletion_requests_status ON data_deletion_requests(clinic_id,status,requested_at);
CREATE INDEX IF NOT EXISTS backup_restore_drills_time ON backup_restore_drills(clinic_id,started_at DESC);
