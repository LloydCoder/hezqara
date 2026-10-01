-- E8: production proving and operating evidence.
CREATE TABLE IF NOT EXISTS slo_definitions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id text REFERENCES clinics(id) ON DELETE CASCADE,
  name text NOT NULL,
  target numeric(8,5) NOT NULL CHECK (target > 0 AND target <= 1),
  window_days integer NOT NULL DEFAULT 30 CHECK (window_days BETWEEN 1 AND 365),
  metric text NOT NULL,
  active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (clinic_id,name)
);

CREATE TABLE IF NOT EXISTS slo_measurements (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id text NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
  slo_id uuid REFERENCES slo_definitions(id) ON DELETE SET NULL,
  window_start timestamptz NOT NULL,
  window_end timestamptz NOT NULL,
  good_events bigint NOT NULL DEFAULT 0 CHECK (good_events >= 0),
  total_events bigint NOT NULL DEFAULT 0 CHECK (total_events >= good_events),
  achieved numeric(8,5) NOT NULL DEFAULT 1,
  evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (window_end >= window_start),
  CHECK (achieved >= 0 AND achieved <= 1)
);

CREATE TABLE IF NOT EXISTS operational_incidents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id text REFERENCES clinics(id) ON DELETE CASCADE,
  severity text NOT NULL CHECK (severity IN ('sev1','sev2','sev3','sev4')),
  status text NOT NULL DEFAULT 'open' CHECK (status IN ('open','contained','recovering','resolved','closed')),
  title text NOT NULL,
  summary text,
  detected_at timestamptz NOT NULL DEFAULT now(),
  resolved_at timestamptz,
  owner_id text,
  root_cause text,
  corrective_actions jsonb NOT NULL DEFAULT '[]'::jsonb,
  evidence jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS operational_changes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id text REFERENCES clinics(id) ON DELETE CASCADE,
  change_type text NOT NULL,
  version text NOT NULL,
  status text NOT NULL CHECK (status IN ('planned','approved','deployed','rolled_back','failed')),
  actor_id text NOT NULL,
  deployed_at timestamptz,
  rollback_at timestamptz,
  evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS recovery_drills (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id text REFERENCES clinics(id) ON DELETE CASCADE,
  drill_type text NOT NULL CHECK (drill_type IN ('backup_restore','service_recovery','worker_recovery','tenant_recovery')),
  started_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  measured_rpo_seconds integer CHECK (measured_rpo_seconds IS NULL OR measured_rpo_seconds >= 0),
  measured_rto_seconds integer CHECK (measured_rto_seconds IS NULL OR measured_rto_seconds >= 0),
  result text NOT NULL DEFAULT 'planned' CHECK (result IN ('planned','passed','failed')),
  evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
  owner_id text NOT NULL
);

CREATE TABLE IF NOT EXISTS worker_heartbeats (
  worker_id text PRIMARY KEY,
  queue text NOT NULL,
  last_seen_at timestamptz NOT NULL DEFAULT now(),
  active_jobs integer NOT NULL DEFAULT 0 CHECK (active_jobs >= 0),
  version text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

ALTER TABLE slo_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE slo_definitions FORCE ROW LEVEL SECURITY;
ALTER TABLE slo_measurements ENABLE ROW LEVEL SECURITY;
ALTER TABLE slo_measurements FORCE ROW LEVEL SECURITY;
ALTER TABLE operational_incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE operational_incidents FORCE ROW LEVEL SECURITY;
ALTER TABLE operational_changes ENABLE ROW LEVEL SECURITY;
ALTER TABLE operational_changes FORCE ROW LEVEL SECURITY;
ALTER TABLE recovery_drills ENABLE ROW LEVEL SECURITY;
ALTER TABLE recovery_drills FORCE ROW LEVEL SECURITY;
ALTER TABLE worker_heartbeats ENABLE ROW LEVEL SECURITY;
ALTER TABLE worker_heartbeats FORCE ROW LEVEL SECURITY;

REVOKE ALL ON slo_definitions,slo_measurements,operational_incidents,operational_changes,recovery_drills,worker_heartbeats FROM anon;
GRANT SELECT,INSERT,UPDATE,DELETE ON slo_definitions,slo_measurements,operational_incidents,operational_changes,recovery_drills,worker_heartbeats TO authenticated;

DROP POLICY IF EXISTS e8_slo_definition_tenant ON slo_definitions;
CREATE POLICY e8_slo_definition_tenant ON slo_definitions AS RESTRICTIVE FOR ALL TO authenticated
USING (clinic_id IS NULL OR clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IS NULL OR clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

DROP POLICY IF EXISTS e8_slo_measurement_tenant ON slo_measurements;
CREATE POLICY e8_slo_measurement_tenant ON slo_measurements AS RESTRICTIVE FOR ALL TO authenticated
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

DROP POLICY IF EXISTS e8_incident_tenant ON operational_incidents;
CREATE POLICY e8_incident_tenant ON operational_incidents AS RESTRICTIVE FOR ALL TO authenticated
USING (clinic_id IS NULL OR clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IS NULL OR clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

DROP POLICY IF EXISTS e8_change_tenant ON operational_changes;
CREATE POLICY e8_change_tenant ON operational_changes AS RESTRICTIVE FOR ALL TO authenticated
USING (clinic_id IS NULL OR clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IS NULL OR clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

DROP POLICY IF EXISTS e8_recovery_tenant ON recovery_drills;
CREATE POLICY e8_recovery_tenant ON recovery_drills AS RESTRICTIVE FOR ALL TO authenticated
USING (clinic_id IS NULL OR clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IS NULL OR clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

DROP POLICY IF EXISTS e8_heartbeat_platform ON worker_heartbeats;
CREATE POLICY e8_heartbeat_platform ON worker_heartbeats AS RESTRICTIVE FOR ALL TO authenticated
USING (true) WITH CHECK (true);

CREATE INDEX IF NOT EXISTS slo_measurements_tenant_window ON slo_measurements(clinic_id,window_end DESC);
CREATE INDEX IF NOT EXISTS operational_incidents_tenant_time ON operational_incidents(clinic_id,detected_at DESC);
CREATE INDEX IF NOT EXISTS operational_changes_tenant_time ON operational_changes(clinic_id,created_at DESC);
CREATE INDEX IF NOT EXISTS recovery_drills_tenant_time ON recovery_drills(clinic_id,started_at DESC);
CREATE INDEX IF NOT EXISTS worker_heartbeats_seen ON worker_heartbeats(last_seen_at DESC);
