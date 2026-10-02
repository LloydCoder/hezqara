-- Migration 049: E11 insurance and authorization workforce hardening.

CREATE UNIQUE INDEX IF NOT EXISTS authorizations_clinic_id_uidx ON authorizations(clinic_id,id);

ALTER TABLE authorizations ADD COLUMN IF NOT EXISTS idempotency_key TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS authorizations_clinic_idempotency_uidx
ON authorizations(clinic_id,idempotency_key)
WHERE idempotency_key IS NOT NULL;

ALTER TABLE eligibility_requests ADD COLUMN IF NOT EXISTS benefits JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS coverage_benefits (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    coverage_id TEXT NOT NULL REFERENCES patient_coverages(id) ON DELETE CASCADE,
    service_code TEXT,
    category TEXT NOT NULL,
    in_network BOOLEAN,
    copay NUMERIC(12,2),
    coinsurance_percent NUMERIC(5,2) CHECK (coinsurance_percent >= 0 AND coinsurance_percent <= 100),
    deductible_remaining NUMERIC(12,2),
    out_of_pocket_remaining NUMERIC(12,2),
    notes TEXT,
    effective_date DATE,
    termination_date DATE,
    source TEXT NOT NULL DEFAULT 'manual',
    last_verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (clinic_id,coverage_id,service_code,category)
);

CREATE TABLE IF NOT EXISTS authorization_documents (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    authorization_id TEXT NOT NULL,
    record_id TEXT REFERENCES records_v2(id) ON DELETE SET NULL,
    document_type TEXT NOT NULL,
    required BOOLEAN NOT NULL DEFAULT TRUE,
    status TEXT NOT NULL DEFAULT 'missing'
      CHECK (status IN ('missing','received','verified','rejected')),
    provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT authorization_documents_authorization_tenant_fk
      FOREIGN KEY (clinic_id,authorization_id) REFERENCES authorizations(clinic_id,id)
);

CREATE TABLE IF NOT EXISTS authorization_events (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    authorization_id TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT NOT NULL,
    actor TEXT,
    reason TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT authorization_events_authorization_tenant_fk
      FOREIGN KEY (clinic_id,authorization_id) REFERENCES authorizations(clinic_id,id)
);

CREATE TABLE IF NOT EXISTS payer_adapter_registry (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    payer_name TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'manual'
      CHECK (mode IN ('manual','fhir','x12','vendor')),
    endpoint_url TEXT,
    secret_ref TEXT,
    capabilities JSONB NOT NULL DEFAULT '{}'::jsonb,
    active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (clinic_id,payer_name)
);

ALTER TABLE coverage_benefits ENABLE ROW LEVEL SECURITY;
ALTER TABLE coverage_benefits FORCE ROW LEVEL SECURITY;
CREATE POLICY coverage_benefits_isolation ON coverage_benefits
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

ALTER TABLE authorization_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE authorization_documents FORCE ROW LEVEL SECURITY;
CREATE POLICY authorization_documents_isolation ON authorization_documents
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

ALTER TABLE authorization_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE authorization_events FORCE ROW LEVEL SECURITY;
CREATE POLICY authorization_events_isolation ON authorization_events
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

ALTER TABLE payer_adapter_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE payer_adapter_registry FORCE ROW LEVEL SECURITY;
CREATE POLICY payer_adapter_registry_isolation ON payer_adapter_registry
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

GRANT SELECT,INSERT,UPDATE,DELETE ON patient_coverages,eligibility_requests,authorizations,records_v2 TO authenticated;
GRANT SELECT,INSERT,UPDATE,DELETE ON coverage_benefits,authorization_documents,authorization_events,payer_adapter_registry TO authenticated;

CREATE INDEX IF NOT EXISTS idx_e11_benefits_coverage ON coverage_benefits(clinic_id,coverage_id,category);
CREATE INDEX IF NOT EXISTS idx_e11_auth_docs_auth ON authorization_documents(clinic_id,authorization_id,status);
CREATE INDEX IF NOT EXISTS idx_e11_auth_events_auth ON authorization_events(clinic_id,authorization_id,created_at DESC);

-- Reassert the tenant policy on pre-existing E11 tables because these are directly
-- reachable by the new authenticated API surface.
DO $$
DECLARE t TEXT;
BEGIN
  FOR t IN SELECT unnest(ARRAY['patient_coverages','eligibility_requests','authorizations','records_v2']) LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t);
    EXECUTE format('DROP POLICY IF EXISTS e11_tenant_select ON %I',t);
    EXECUTE format('DROP POLICY IF EXISTS e11_tenant_write ON %I',t);
    EXECUTE format('CREATE POLICY e11_tenant_select ON %I FOR SELECT TO authenticated USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))',t);
    EXECUTE format('CREATE POLICY e11_tenant_write ON %I FOR INSERT, UPDATE, DELETE TO authenticated USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true))) WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))',t);
  END LOOP;
END $$;
