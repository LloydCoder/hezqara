CREATE TABLE IF NOT EXISTS workforce_runs (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 workforce_key TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'queued' CHECK(status IN ('queued','running','waiting_approval','completed','failed','cancelled')),
 context JSONB NOT NULL DEFAULT '{}'::jsonb,
 current_stage TEXT,
 approval_required BOOLEAN NOT NULL DEFAULT false,
 failure_class TEXT,
 idempotency_key TEXT NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), started_at TIMESTAMPTZ, completed_at TIMESTAMPTZ,
 CONSTRAINT workforce_runs_clinic_id_uidx UNIQUE(clinic_id,id), CONSTRAINT workforce_runs_idempotency_uk UNIQUE(clinic_id,idempotency_key)
);
ALTER TABLE workforce_runs ENABLE ROW LEVEL SECURITY; ALTER TABLE workforce_runs FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS workforce_runs_isolation ON workforce_runs;
CREATE POLICY workforce_runs_isolation ON workforce_runs USING(clinic_id IN(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK(clinic_id IN(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
GRANT SELECT,INSERT,UPDATE,DELETE ON workforce_runs TO authenticated;
CREATE INDEX IF NOT EXISTS idx_workforce_runs_status ON workforce_runs(clinic_id,status,updated_at DESC);
