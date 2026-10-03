CREATE TABLE IF NOT EXISTS reliability_targets (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 service_key TEXT NOT NULL,
 slo_target NUMERIC(6,5) NOT NULL CHECK(slo_target>0 AND slo_target<=1),
 rto_seconds INTEGER NOT NULL CHECK(rto_seconds>0),
 rpo_seconds INTEGER NOT NULL CHECK(rpo_seconds>=0),
 max_concurrency INTEGER,
 status TEXT NOT NULL DEFAULT 'defined' CHECK(status IN ('defined','validated','exception')),
 evidence_ref TEXT,
 last_tested_at TIMESTAMPTZ,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 CONSTRAINT reliability_targets_clinic_id_uidx UNIQUE(clinic_id,id), CONSTRAINT reliability_targets_key_uk UNIQUE(clinic_id,service_key)
);
ALTER TABLE reliability_targets ENABLE ROW LEVEL SECURITY; ALTER TABLE reliability_targets FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS reliability_targets_isolation ON reliability_targets;
CREATE POLICY reliability_targets_isolation ON reliability_targets USING(clinic_id IN(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK(clinic_id IN(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
GRANT SELECT,INSERT,UPDATE,DELETE ON reliability_targets TO authenticated;
CREATE INDEX IF NOT EXISTS idx_reliability_targets_status ON reliability_targets(clinic_id,status);
