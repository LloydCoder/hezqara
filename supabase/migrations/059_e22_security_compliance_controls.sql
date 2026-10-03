CREATE TABLE IF NOT EXISTS compliance_controls (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 framework TEXT NOT NULL,
 control_key TEXT NOT NULL,
 title TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'planned' CHECK(status IN ('planned','implemented','evidenced','exception')),
 owner TEXT,
 evidence_ref TEXT,
 last_reviewed_at TIMESTAMPTZ,
 notes TEXT,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 CONSTRAINT compliance_controls_clinic_id_uidx UNIQUE(clinic_id,id), CONSTRAINT compliance_controls_key_uk UNIQUE(clinic_id,framework,control_key)
);
ALTER TABLE compliance_controls ENABLE ROW LEVEL SECURITY; ALTER TABLE compliance_controls FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS compliance_controls_isolation ON compliance_controls;
CREATE POLICY compliance_controls_isolation ON compliance_controls USING(clinic_id IN(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK(clinic_id IN(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
GRANT SELECT,INSERT,UPDATE,DELETE ON compliance_controls TO authenticated;
CREATE INDEX IF NOT EXISTS idx_compliance_controls_status ON compliance_controls(clinic_id,framework,status);
