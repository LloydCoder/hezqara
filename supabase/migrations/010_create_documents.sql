-- Migration 010: Medical documents / records
CREATE TABLE IF NOT EXISTS documents (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id       TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_id      TEXT REFERENCES patients(id),
    call_id         TEXT REFERENCES calls(id),
    document_type   TEXT NOT NULL,
    filename        TEXT,
    r2_key          TEXT,
    mime_type       TEXT,
    size_bytes      INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY documents_isolation ON documents
    USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id = current_setting('app.clerk_org_id', true)));
