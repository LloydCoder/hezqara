-- Migration 011: HIPAA audit log
-- Append-only. No RLS deletion. Every PHI access recorded.
CREATE TABLE IF NOT EXISTS audit_log (
    id              BIGSERIAL PRIMARY KEY,
    event_type      TEXT NOT NULL,
    clinic_id       TEXT NOT NULL,
    call_id         TEXT,
    patient_id      TEXT,
    agent_type      TEXT,
    action          TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_audit_clinic ON audit_log(clinic_id);
CREATE INDEX idx_audit_patient ON audit_log(patient_id);
CREATE INDEX idx_audit_created ON audit_log(created_at);
