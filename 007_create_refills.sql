-- Migration 007: Medication refill requests
CREATE TABLE IF NOT EXISTS refill_requests (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id       TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_id      TEXT NOT NULL REFERENCES patients(id),
    call_id         TEXT REFERENCES calls(id),
    medication_name TEXT NOT NULL,
    dose            TEXT,
    pharmacy_name   TEXT,
    pharmacy_phone  TEXT,
    status          TEXT DEFAULT 'pending' CHECK (status IN ('pending','approved','denied','sent')),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE refill_requests ENABLE ROW LEVEL SECURITY;
CREATE POLICY refills_isolation ON refill_requests
    USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id = current_setting('app.clerk_org_id', true)));
CREATE INDEX idx_refills_clinic ON refill_requests(clinic_id);
