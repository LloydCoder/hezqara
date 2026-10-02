-- Migration 052: E14 document, fax and referral intelligence.

CREATE UNIQUE INDEX IF NOT EXISTS documents_clinic_id_uidx ON documents(clinic_id,id);
CREATE UNIQUE INDEX IF NOT EXISTS referrals_v2_clinic_id_uidx ON referrals_v2(clinic_id,id);

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents FORCE ROW LEVEL SECURITY;
GRANT SELECT,INSERT,UPDATE,DELETE ON documents TO authenticated;

CREATE TABLE IF NOT EXISTS document_intake_items (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_id TEXT,
    source TEXT NOT NULL CHECK(source IN ('fax','email','upload','ehr','api')),
    external_reference TEXT,
    filename TEXT,
    mime_type TEXT,
    content_hash TEXT,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'received'
      CHECK(status IN ('received','classified','needs_match','matched','routed','review_required','rejected','completed')),
    classification TEXT,
    confidence NUMERIC(5,4) CHECK(confidence >= 0 AND confidence <= 1),
    extracted JSONB NOT NULL DEFAULT '{}'::jsonb,
    provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT document_intake_patient_tenant_fk
      FOREIGN KEY (clinic_id,patient_id) REFERENCES patients(clinic_id,id)
);
CREATE UNIQUE INDEX IF NOT EXISTS document_intake_dedupe_uidx
ON document_intake_items(clinic_id,content_hash)
WHERE content_hash IS NOT NULL;

CREATE TABLE IF NOT EXISTS document_routes (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    intake_id TEXT NOT NULL,
    target_type TEXT NOT NULL CHECK(target_type IN ('patient_record','authorization','referral','claim','task','review_queue')),
    target_id TEXT,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'queued'
      CHECK(status IN ('queued','routed','failed','cancelled')),
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT document_routes_intake_tenant_fk
      FOREIGN KEY (clinic_id,intake_id) REFERENCES document_intake_items(clinic_id,id)
);

CREATE TABLE IF NOT EXISTS document_extractions (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    intake_id TEXT NOT NULL,
    field_name TEXT NOT NULL,
    value JSONB NOT NULL,
    confidence NUMERIC(5,4) CHECK(confidence >= 0 AND confidence <= 1),
    source_ref TEXT,
    extractor_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT document_extractions_intake_tenant_fk
      FOREIGN KEY (clinic_id,intake_id) REFERENCES document_intake_items(clinic_id,id)
);

CREATE TABLE IF NOT EXISTS referral_events (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    referral_id TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT NOT NULL,
    actor TEXT,
    reason TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT referral_events_referral_tenant_fk
      FOREIGN KEY (clinic_id,referral_id) REFERENCES referrals_v2(clinic_id,id)
);

ALTER TABLE document_intake_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_intake_items FORCE ROW LEVEL SECURITY;
CREATE POLICY document_intake_items_isolation ON document_intake_items
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

ALTER TABLE document_routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_routes FORCE ROW LEVEL SECURITY;
CREATE POLICY document_routes_isolation ON document_routes
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

ALTER TABLE document_extractions ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_extractions FORCE ROW LEVEL SECURITY;
CREATE POLICY document_extractions_isolation ON document_extractions
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

ALTER TABLE referral_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE referral_events FORCE ROW LEVEL SECURITY;
CREATE POLICY referral_events_isolation ON referral_events
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

GRANT SELECT,INSERT,UPDATE,DELETE ON document_intake_items,document_routes,document_extractions,referral_events TO authenticated;

CREATE INDEX IF NOT EXISTS idx_e14_intake_status ON document_intake_items(clinic_id,status,received_at DESC);
CREATE INDEX IF NOT EXISTS idx_e14_intake_patient ON document_intake_items(clinic_id,patient_id,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_e14_routes_intake ON document_routes(clinic_id,intake_id,status);
CREATE INDEX IF NOT EXISTS idx_e14_extractions_intake ON document_extractions(clinic_id,intake_id,field_name);
CREATE INDEX IF NOT EXISTS idx_e14_referral_events ON referral_events(clinic_id,referral_id,created_at DESC);
