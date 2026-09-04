-- Migration 004: Call logs

CREATE TABLE IF NOT EXISTS calls (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id       TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_id      TEXT REFERENCES patients(id),
    retell_call_id  TEXT UNIQUE,
    call_type       TEXT DEFAULT 'inbound',
    from_number     TEXT,
    to_number       TEXT,
    duration_ms     INTEGER,
    intent          TEXT,
    outcome         TEXT,
    agent_type      TEXT DEFAULT 'reception',
    recording_r2_key TEXT,
    transcript      JSONB,
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE calls ENABLE ROW LEVEL SECURITY;
CREATE POLICY calls_clinic_isolation ON calls
    USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id = current_setting('app.clerk_org_id', true)));
CREATE INDEX idx_calls_clinic ON calls(clinic_id);
CREATE INDEX idx_calls_patient ON calls(patient_id);
CREATE INDEX idx_calls_retell ON calls(retell_call_id);
