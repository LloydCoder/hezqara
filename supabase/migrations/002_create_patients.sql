-- Migration 002: Patients table
-- PHI stored here. RLS enforces clinic isolation.

CREATE TABLE IF NOT EXISTS patients (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id       TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    ehr_patient_id  TEXT,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    date_of_birth   DATE,
    phone           TEXT,
    email           TEXT,
    address_street  TEXT,
    address_city    TEXT,
    address_state   TEXT,
    address_zip     TEXT,
    insurance_carrier TEXT,
    insurance_member_id TEXT,
    insurance_group TEXT,
    uninsured       BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE patients ENABLE ROW LEVEL SECURITY;

CREATE POLICY patients_clinic_isolation ON patients
    USING (clinic_id IN (
        SELECT id FROM clinics
        WHERE clerk_org_id = current_setting('app.clerk_org_id', true)
    ));

CREATE INDEX idx_patients_clinic ON patients(clinic_id);
CREATE INDEX idx_patients_ehr_id ON patients(ehr_patient_id);
CREATE INDEX idx_patients_phone ON patients(phone);
