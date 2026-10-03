-- Migration 054: E16 documentation intelligence.

CREATE TABLE IF NOT EXISTS documentation_quality_checks (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL CHECK(source_type IN ('clinical_note','scribe_note','record')),
    source_ref TEXT,
    score NUMERIC(6,5) NOT NULL CHECK(score >= 0 AND score <= 1),
    summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    ruleset_version TEXT NOT NULL DEFAULT 'e16.v1',
    model_version TEXT NOT NULL DEFAULT 'deterministic-e16.v1',
    status TEXT NOT NULL DEFAULT 'review' CHECK(status IN ('review','accepted','dismissed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS documentation_insights (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    quality_check_id TEXT NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('completeness','follow_up','uncertainty','coding_support','longitudinal')),
    key TEXT NOT NULL,
    detail TEXT NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('info','warning','critical')),
    confidence NUMERIC(6,5) NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
    source_ref TEXT,
    status TEXT NOT NULL DEFAULT 'proposed' CHECK(status IN ('proposed','accepted','dismissed')),
    provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT documentation_insights_check_tenant_fk
      FOREIGN KEY (clinic_id,quality_check_id) REFERENCES documentation_quality_checks(clinic_id,id)
);

ALTER TABLE documentation_quality_checks ENABLE ROW LEVEL SECURITY;
ALTER TABLE documentation_quality_checks FORCE ROW LEVEL SECURITY;
CREATE POLICY documentation_quality_checks_isolation ON documentation_quality_checks
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

ALTER TABLE documentation_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE documentation_insights FORCE ROW LEVEL SECURITY;
CREATE POLICY documentation_insights_isolation ON documentation_insights
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

GRANT SELECT,INSERT,UPDATE,DELETE ON documentation_quality_checks,documentation_insights TO authenticated;

CREATE INDEX IF NOT EXISTS idx_e16_quality_checks ON documentation_quality_checks(clinic_id,status,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_e16_insights_check ON documentation_insights(clinic_id,quality_check_id,status);
CREATE INDEX IF NOT EXISTS idx_e16_insights_source ON documentation_insights(clinic_id,source_ref,created_at DESC);
