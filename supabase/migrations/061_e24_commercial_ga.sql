CREATE TABLE IF NOT EXISTS commercial_plans (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 plan_key TEXT NOT NULL,
 monthly_price_cents INTEGER NOT NULL CHECK(monthly_price_cents>=0),
 included_providers INTEGER NOT NULL CHECK(included_providers>0),
 included_encounters INTEGER,
 included_scribe_minutes INTEGER,
 status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','active','retired')),
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 CONSTRAINT commercial_plans_clinic_id_uidx UNIQUE(clinic_id,id), CONSTRAINT commercial_plans_key_uk UNIQUE(clinic_id,plan_key)
);
CREATE TABLE IF NOT EXISTS launch_gates (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 gate_key TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'blocked' CHECK(status IN ('blocked','ready','waived')),
 evidence_ref TEXT,
 owner TEXT,
 notes TEXT,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 CONSTRAINT launch_gates_clinic_id_uidx UNIQUE(clinic_id,id), CONSTRAINT launch_gates_key_uk UNIQUE(clinic_id,gate_key)
);
ALTER TABLE commercial_plans ENABLE ROW LEVEL SECURITY; ALTER TABLE commercial_plans FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS commercial_plans_isolation ON commercial_plans;
CREATE POLICY commercial_plans_isolation ON commercial_plans USING(clinic_id IN(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK(clinic_id IN(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
ALTER TABLE launch_gates ENABLE ROW LEVEL SECURITY; ALTER TABLE launch_gates FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS launch_gates_isolation ON launch_gates;
CREATE POLICY launch_gates_isolation ON launch_gates USING(clinic_id IN(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK(clinic_id IN(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
GRANT SELECT,INSERT,UPDATE,DELETE ON commercial_plans,launch_gates TO authenticated;
CREATE INDEX IF NOT EXISTS idx_launch_gates_status ON launch_gates(clinic_id,status,updated_at DESC);
