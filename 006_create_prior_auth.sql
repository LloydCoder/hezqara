-- Migration 006: Prior authorization records

CREATE TABLE IF NOT EXISTS prior_auth_records (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id       TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_id      TEXT NOT NULL REFERENCES patients(id),
    call_id         TEXT REFERENCES calls(id),
    tracking_number TEXT,
    service_code    TEXT NOT NULL,
    diagnosis_codes TEXT[],
    payer_name      TEXT,
    status          TEXT DEFAULT 'pending'
                        CHECK (status IN ('pending','approved','denied','more_info','cancelled')),
    denial_reason   TEXT,
    approved_units  INTEGER,
    valid_from      DATE,
    valid_until     DATE,
    submitted_at    TIMESTAMPTZ DEFAULT NOW(),
    decision_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE prior_auth_records ENABLE ROW LEVEL SECURITY;
CREATE POLICY prior_auth_clinic_isolation ON prior_auth_records
    USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id = current_setting('app.clerk_org_id', true)));
CREATE INDEX idx_prior_auth_clinic ON prior_auth_records(clinic_id);
CREATE INDEX idx_prior_auth_status ON prior_auth_records(status);
CREATE INDEX idx_prior_auth_tracking ON prior_auth_records(tracking_number);
