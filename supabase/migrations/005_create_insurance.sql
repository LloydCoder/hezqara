-- Migration 005: Insurance verification records

CREATE TABLE IF NOT EXISTS insurance_records (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id       TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_id      TEXT NOT NULL REFERENCES patients(id),
    call_id         TEXT REFERENCES calls(id),
    member_id       TEXT,
    carrier         TEXT,
    plan_type       TEXT,
    eligible        BOOLEAN,
    copay_primary   INTEGER,
    copay_specialist INTEGER,
    deductible_annual INTEGER,
    deductible_met  INTEGER,
    out_of_pocket_max INTEGER,
    in_network      BOOLEAN,
    verified_at     TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE insurance_records ENABLE ROW LEVEL SECURITY;
CREATE POLICY insurance_clinic_isolation ON insurance_records
    USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id = current_setting('app.clerk_org_id', true)));
CREATE INDEX idx_insurance_clinic ON insurance_records(clinic_id);
CREATE INDEX idx_insurance_patient ON insurance_records(patient_id);
