-- Migration 008: Referral tracking
CREATE TABLE IF NOT EXISTS referrals (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id           TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_id          TEXT NOT NULL REFERENCES patients(id),
    call_id             TEXT REFERENCES calls(id),
    referring_provider  TEXT,
    specialist_name     TEXT,
    specialty           TEXT,
    reason              TEXT,
    status              TEXT DEFAULT 'initiated' CHECK (status IN ('initiated','sent','accepted','scheduled','completed')),
    appointment_date    DATE,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE referrals ENABLE ROW LEVEL SECURITY;
CREATE POLICY referrals_isolation ON referrals
    USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id = current_setting('app.clerk_org_id', true)));
CREATE INDEX idx_referrals_clinic ON referrals(clinic_id);
