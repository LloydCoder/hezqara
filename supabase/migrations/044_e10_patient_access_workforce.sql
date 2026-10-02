-- Migration 044: E10 patient access workforce foundation
-- Schedule/Slot/Appointment-aligned access primitives, tenant isolated.

CREATE TABLE IF NOT EXISTS patient_access_requests (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_id TEXT REFERENCES patients(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'new'
        CHECK (status IN ('new','in_progress','ready','escalated','completed','cancelled')),
    channel TEXT NOT NULL DEFAULT 'staff'
        CHECK (channel IN ('staff','patient_portal','phone','sms','email','agent','api')),
    request_type TEXT NOT NULL
        CHECK (request_type IN ('new_patient','appointment','intake','registration','access_question')),
    reason TEXT,
    requested_start TIMESTAMPTZ,
    requested_end TIMESTAMPTZ,
    assigned_agent TEXT,
    idempotency_key TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (clinic_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS patient_intake_submissions (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_id TEXT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    access_request_id TEXT REFERENCES patient_access_requests(id) ON DELETE SET NULL,
    form_version TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft','submitted','reviewed','superseded')),
    responses JSONB NOT NULL DEFAULT '{}'::jsonb,
    submitted_by TEXT,
    submitted_at TIMESTAMPTZ,
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS provider_schedules (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    provider_id TEXT NOT NULL,
    service_type TEXT,
    specialty TEXT,
    timezone TEXT NOT NULL DEFAULT 'America/New_York',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    planning_start TIMESTAMPTZ,
    planning_end TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS schedule_slots (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    schedule_id TEXT NOT NULL REFERENCES provider_schedules(id) ON DELETE CASCADE,
    provider_id TEXT NOT NULL,
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'free'
        CHECK (status IN ('free','busy','busy-unavailable','busy-tentative','entered-in-error')),
    appointment_id TEXT REFERENCES appointments(id) ON DELETE SET NULL,
    overbooked BOOLEAN NOT NULL DEFAULT FALSE,
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (ends_at > starts_at)
);

CREATE TABLE IF NOT EXISTS waitlist_entries (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_id TEXT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    provider_id TEXT,
    service_type TEXT,
    requested_start TIMESTAMPTZ,
    requested_end TIMESTAMPTZ,
    priority INTEGER NOT NULL DEFAULT 100 CHECK (priority >= 0),
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active','contacted','booked','cancelled','expired')),
    notification_channel TEXT DEFAULT 'sms'
        CHECK (notification_channel IN ('sms','email','phone','portal','none')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE appointments ADD COLUMN IF NOT EXISTS slot_id TEXT REFERENCES schedule_slots(id) ON DELETE SET NULL;

ALTER TABLE patient_access_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_access_requests FORCE ROW LEVEL SECURITY;
CREATE POLICY patient_access_requests_isolation ON patient_access_requests
    USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id = current_setting('app.clerk_org_id', true)))
    WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id = current_setting('app.clerk_org_id', true)));

ALTER TABLE patient_intake_submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_intake_submissions FORCE ROW LEVEL SECURITY;
CREATE POLICY patient_intake_submissions_isolation ON patient_intake_submissions
    USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id = current_setting('app.clerk_org_id', true)))
    WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id = current_setting('app.clerk_org_id', true)));

ALTER TABLE provider_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE provider_schedules FORCE ROW LEVEL SECURITY;
CREATE POLICY provider_schedules_isolation ON provider_schedules
    USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id = current_setting('app.clerk_org_id', true)))
    WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id = current_setting('app.clerk_org_id', true)));

ALTER TABLE schedule_slots ENABLE ROW LEVEL SECURITY;
ALTER TABLE schedule_slots FORCE ROW LEVEL SECURITY;
CREATE POLICY schedule_slots_isolation ON schedule_slots
    USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id = current_setting('app.clerk_org_id', true)))
    WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id = current_setting('app.clerk_org_id', true)));

ALTER TABLE waitlist_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE waitlist_entries FORCE ROW LEVEL SECURITY;
CREATE POLICY waitlist_entries_isolation ON waitlist_entries
    USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id = current_setting('app.clerk_org_id', true)))
    WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id = current_setting('app.clerk_org_id', true)));

CREATE INDEX idx_access_requests_clinic_status ON patient_access_requests(clinic_id,status,created_at DESC);
CREATE INDEX idx_access_requests_patient ON patient_access_requests(clinic_id,patient_id);
CREATE INDEX idx_intake_patient ON patient_intake_submissions(clinic_id,patient_id,created_at DESC);
CREATE INDEX idx_provider_schedules_clinic ON provider_schedules(clinic_id,provider_id,active);
CREATE INDEX idx_schedule_slots_window ON schedule_slots(clinic_id,provider_id,starts_at,status);
CREATE INDEX idx_waitlist_matching ON waitlist_entries(clinic_id,provider_id,status,priority,requested_start);

COMMENT ON TABLE patient_access_requests IS 'E10 governed patient-access work queue; AI may assist but cannot bypass authorization or clinical authority.';
COMMENT ON TABLE patient_intake_submissions IS 'E10 structured pre-visit intake; responses are untrusted patient-provided data until reviewed.';
COMMENT ON TABLE provider_schedules IS 'E10 schedule containers aligned with FHIR Schedule semantics.';
COMMENT ON TABLE schedule_slots IS 'E10 bookable availability aligned with FHIR Slot semantics.';
COMMENT ON TABLE waitlist_entries IS 'E10 governed waitlist requests for appointment availability.';
