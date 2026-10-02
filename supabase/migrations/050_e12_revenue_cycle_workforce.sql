-- Migration 050: E12 revenue cycle workforce hardening.

CREATE UNIQUE INDEX IF NOT EXISTS claims_clinic_id_uidx ON claims(clinic_id,id);

ALTER TABLE claims ADD COLUMN IF NOT EXISTS creation_idempotency_key TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS claims_clinic_creation_idempotency_uidx
ON claims(clinic_id,creation_idempotency_key)
WHERE creation_idempotency_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS claim_scrub_results (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    claim_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('passed','failed','warning')),
    issues JSONB NOT NULL DEFAULT '[]'::jsonb,
    ruleset_version TEXT NOT NULL DEFAULT 'e12.v1',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT claim_scrub_results_claim_tenant_fk
      FOREIGN KEY (clinic_id,claim_id) REFERENCES claims(clinic_id,id)
);

CREATE TABLE IF NOT EXISTS claim_submission_attempts (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    claim_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    transport TEXT NOT NULL DEFAULT 'adapter',
    status TEXT NOT NULL CHECK(status IN ('queued','submitted','accepted','rejected','failed')),
    external_reference TEXT,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(clinic_id,idempotency_key),
    CONSTRAINT claim_submission_attempts_claim_tenant_fk
      FOREIGN KEY (clinic_id,claim_id) REFERENCES claims(clinic_id,id)
);

CREATE TABLE IF NOT EXISTS claim_events (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    claim_id TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT NOT NULL,
    actor TEXT,
    reason TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT claim_events_claim_tenant_fk
      FOREIGN KEY (clinic_id,claim_id) REFERENCES claims(clinic_id,id)
);

CREATE TABLE IF NOT EXISTS denial_appeals (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    denial_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft'
      CHECK(status IN ('draft','ready','submitted','accepted','denied','closed')),
    argument TEXT,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    submission_reference TEXT,
    submitted_at TIMESTAMPTZ,
    response_at TIMESTAMPTZ,
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT denial_appeals_denial_tenant_fk
      FOREIGN KEY (clinic_id,denial_id) REFERENCES denials(clinic_id,id)
);

ALTER TABLE claim_scrub_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE claim_scrub_results FORCE ROW LEVEL SECURITY;
CREATE POLICY claim_scrub_results_isolation ON claim_scrub_results
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

ALTER TABLE claim_submission_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE claim_submission_attempts FORCE ROW LEVEL SECURITY;
CREATE POLICY claim_submission_attempts_isolation ON claim_submission_attempts
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

ALTER TABLE claim_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE claim_events FORCE ROW LEVEL SECURITY;
CREATE POLICY claim_events_isolation ON claim_events
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

ALTER TABLE denial_appeals ENABLE ROW LEVEL SECURITY;
ALTER TABLE denial_appeals FORCE ROW LEVEL SECURITY;
CREATE POLICY denial_appeals_isolation ON denial_appeals
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

GRANT SELECT,INSERT,UPDATE,DELETE
ON claims,claim_lines,claim_adjudications,ar_work_items,denials,
   claim_scrub_results,claim_submission_attempts,claim_events,denial_appeals
TO authenticated;

CREATE INDEX IF NOT EXISTS idx_e12_scrub_claim ON claim_scrub_results(clinic_id,claim_id,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_e12_submission_claim ON claim_submission_attempts(clinic_id,claim_id,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_e12_claim_events_claim ON claim_events(clinic_id,claim_id,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_e12_appeals_denial ON denial_appeals(clinic_id,denial_id,created_at DESC);
