-- Migration 003: Appointments table

CREATE TABLE IF NOT EXISTS appointments (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id           TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_id          TEXT NOT NULL REFERENCES patients(id),
    ehr_appointment_id  TEXT,
    provider_id         TEXT,
    provider_name       TEXT,
    appointment_datetime TIMESTAMPTZ NOT NULL,
    duration_minutes    INTEGER DEFAULT 20,
    reason              TEXT,
    status              TEXT DEFAULT 'scheduled'
                            CHECK (status IN ('scheduled','confirmed','completed','cancelled','no_show')),
    booked_by_agent     TEXT DEFAULT 'scheduling',
    call_id             TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;

CREATE POLICY appointments_clinic_isolation ON appointments
    USING (clinic_id IN (
        SELECT id FROM clinics
        WHERE clerk_org_id = current_setting('app.clerk_org_id', true)
    ));

CREATE INDEX idx_appointments_clinic ON appointments(clinic_id);
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_datetime ON appointments(appointment_datetime);
CREATE INDEX idx_appointments_status ON appointments(status);
