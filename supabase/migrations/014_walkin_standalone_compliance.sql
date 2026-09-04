-- Migration 014: Walk-In Check-In + Standalone Mode + Cross-Border Consent
-- Covers tables required by app/walkin/* and app/standalone/* which had
-- code but no backing schema. Fixes gap identified in deep audit.

-- ── Walk-in visits (queue-based, not appointment-based) ─────────────────────
CREATE TABLE IF NOT EXISTS walkin_visits (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id           TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_id          TEXT REFERENCES patients(id) ON DELETE SET NULL,
    patient_name        TEXT NOT NULL,
    patient_phone       TEXT,
    chief_complaint     TEXT NOT NULL,
    language             TEXT DEFAULT 'en',
    queue_number        INTEGER NOT NULL,
    priority            TEXT DEFAULT 'normal' CHECK (priority IN ('normal', 'urgent', 'emergency')),
    status              TEXT DEFAULT 'waiting' CHECK (status IN ('waiting', 'called', 'completed', 'no_show', 'cancelled')),
    provider_id         TEXT,
    room                TEXT,
    checked_in_at       TIMESTAMPTZ DEFAULT NOW(),
    called_at           TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    notes               TEXT,
    diagnosis           TEXT,
    follow_up_days      INTEGER,
    follow_up_scheduled BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE walkin_visits ENABLE ROW LEVEL SECURITY;

CREATE POLICY walkin_visits_clinic_isolation ON walkin_visits
    USING (clinic_id IN (
        SELECT id FROM clinics
        WHERE clerk_org_id = current_setting('app.clerk_org_id', true)
    ));

CREATE INDEX idx_walkin_clinic ON walkin_visits(clinic_id);
CREATE INDEX idx_walkin_status ON walkin_visits(clinic_id, status);
CREATE INDEX idx_walkin_phone ON walkin_visits(patient_phone);
CREATE INDEX idx_walkin_checked_in ON walkin_visits(clinic_id, checked_in_at DESC);

-- Sequential queue numbering per clinic per day
CREATE OR REPLACE FUNCTION next_queue_number(p_clinic_id TEXT)
RETURNS INTEGER AS $$
DECLARE
    next_num INTEGER;
BEGIN
    SELECT COALESCE(MAX(queue_number), 0) + 1 INTO next_num
    FROM walkin_visits
    WHERE clinic_id = p_clinic_id
      AND checked_in_at::date = CURRENT_DATE;
    RETURN next_num;
END;
$$ LANGUAGE plpgsql;

-- ── QR code registry (per clinic, per language) ──────────────────────────────
CREATE TABLE IF NOT EXISTS walkin_qr_codes (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id           TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    qr_id               TEXT NOT NULL,
    language            TEXT DEFAULT 'en',
    whatsapp_url        TEXT NOT NULL,
    sms_fallback_url    TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(clinic_id, language)
);

ALTER TABLE walkin_qr_codes ENABLE ROW LEVEL SECURITY;

CREATE POLICY walkin_qr_clinic_isolation ON walkin_qr_codes
    USING (clinic_id IN (
        SELECT id FROM clinics
        WHERE clerk_org_id = current_setting('app.clerk_org_id', true)
    ));

CREATE INDEX idx_walkin_qr_clinic ON walkin_qr_codes(clinic_id);

-- ── Standalone patient records (clinics without an EHR) ──────────────────────
-- Distinct from `patients` table: standalone clinics have no EHR write-back,
-- so this is the source of truth rather than a cache of EHR data.
CREATE TABLE IF NOT EXISTS standalone_patients (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id           TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    first_name          TEXT NOT NULL,
    last_name           TEXT NOT NULL,
    phone               TEXT,
    email               TEXT,
    date_of_birth       DATE,
    gender              TEXT,
    address_street      TEXT,
    address_city        TEXT,
    address_country     TEXT,
    language            TEXT DEFAULT 'en',
    notes               TEXT,
    imported_from_csv   BOOLEAN DEFAULT FALSE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE standalone_patients ENABLE ROW LEVEL SECURITY;

CREATE POLICY standalone_patients_clinic_isolation ON standalone_patients
    USING (clinic_id IN (
        SELECT id FROM clinics
        WHERE clerk_org_id = current_setting('app.clerk_org_id', true)
    ));

CREATE INDEX idx_standalone_patients_clinic ON standalone_patients(clinic_id);
CREATE INDEX idx_standalone_patients_phone ON standalone_patients(phone);

-- ── Standalone appointments (no EHR write-back) ──────────────────────────────
CREATE TABLE IF NOT EXISTS standalone_appointments (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id           TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_id          TEXT REFERENCES standalone_patients(id) ON DELETE CASCADE,
    provider_id         TEXT,
    appointment_datetime TIMESTAMPTZ NOT NULL,
    duration_minutes    INTEGER DEFAULT 20,
    reason              TEXT,
    status              TEXT DEFAULT 'confirmed' CHECK (status IN ('confirmed', 'cancelled', 'completed', 'no_show')),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE standalone_appointments ENABLE ROW LEVEL SECURITY;

CREATE POLICY standalone_appointments_clinic_isolation ON standalone_appointments
    USING (clinic_id IN (
        SELECT id FROM clinics
        WHERE clerk_org_id = current_setting('app.clerk_org_id', true)
    ));

CREATE INDEX idx_standalone_appt_clinic ON standalone_appointments(clinic_id);
CREATE INDEX idx_standalone_appt_datetime ON standalone_appointments(clinic_id, appointment_datetime);

-- ── Standalone providers (no EHR provider directory) ─────────────────────────
CREATE TABLE IF NOT EXISTS standalone_providers (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id           TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    specialty           TEXT,
    working_hours       JSONB DEFAULT '{}'::jsonb,
    slot_duration_minutes INTEGER DEFAULT 20,
    break_times         JSONB DEFAULT '[]'::jsonb,
    active              BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE standalone_providers ENABLE ROW LEVEL SECURITY;

CREATE POLICY standalone_providers_clinic_isolation ON standalone_providers
    USING (clinic_id IN (
        SELECT id FROM clinics
        WHERE clerk_org_id = current_setting('app.clerk_org_id', true)
    ));

CREATE INDEX idx_standalone_providers_clinic ON standalone_providers(clinic_id);

-- ── Offline sync queue (Redis-backed in app, persisted here for recovery) ────
-- Power outages and intermittent internet are the #1 cited infrastructure
-- challenge in Nigerian hospitals. Operations queue here so nothing is lost
-- on a process restart, even before Redis sync completes.
CREATE TABLE IF NOT EXISTS offline_sync_queue (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id           TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    operation           TEXT NOT NULL,
    payload             JSONB NOT NULL,
    status              TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'synced', 'failed')),
    queued_at           TIMESTAMPTZ DEFAULT NOW(),
    synced_at           TIMESTAMPTZ,
    retry_count         INTEGER DEFAULT 0,
    last_error          TEXT
);

ALTER TABLE offline_sync_queue ENABLE ROW LEVEL SECURITY;

CREATE POLICY offline_sync_clinic_isolation ON offline_sync_queue
    USING (clinic_id IN (
        SELECT id FROM clinics
        WHERE clerk_org_id = current_setting('app.clerk_org_id', true)
    ));

CREATE INDEX idx_offline_sync_pending ON offline_sync_queue(clinic_id, status) WHERE status = 'pending';

-- ── Cross-border data transfer consent (NDPA s.41-43 requirement) ───────────
-- Nigeria-region clinics storing data in Supabase Frankfurt (EU) must have
-- a documented legal basis for this cross-border transfer. Captured once
-- during onboarding step 5 for Nigeria-region clinics.
CREATE TABLE IF NOT EXISTS cross_border_transfer_consent (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id           TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    destination         TEXT NOT NULL DEFAULT 'Supabase Frankfurt (EU)',
    legal_basis         TEXT NOT NULL CHECK (legal_basis IN (
                            'binding_corporate_rules', 'ndpc_approved_scc', 'explicit_consent'
                         )),
    consented_at        TIMESTAMPTZ DEFAULT NOW(),
    consented_by_name   TEXT,
    consented_by_title  TEXT,
    law_reference        TEXT DEFAULT 'Nigeria Data Protection Act, 2023 s.41-43',
    UNIQUE(clinic_id)
);

ALTER TABLE cross_border_transfer_consent ENABLE ROW LEVEL SECURITY;

CREATE POLICY cross_border_consent_clinic_isolation ON cross_border_transfer_consent
    USING (clinic_id IN (
        SELECT id FROM clinics
        WHERE clerk_org_id = current_setting('app.clerk_org_id', true)
    ));

-- ── WhatsApp template messages (Meta-approved utility templates) ────────────
-- Follow-up reminders and "called to see doctor" notifications sent outside
-- the 24h free service window require pre-approved utility templates.
-- This table tracks Meta approval status per template per language.
CREATE TABLE IF NOT EXISTS whatsapp_templates (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    template_name       TEXT NOT NULL,
    language            TEXT NOT NULL,
    category            TEXT NOT NULL DEFAULT 'utility' CHECK (category IN ('utility', 'marketing', 'authentication')),
    body_text           TEXT NOT NULL,
    meta_template_id    TEXT,
    approval_status     TEXT DEFAULT 'pending' CHECK (approval_status IN ('pending', 'approved', 'rejected')),
    submitted_at        TIMESTAMPTZ DEFAULT NOW(),
    approved_at         TIMESTAMPTZ,
    UNIQUE(template_name, language)
);

CREATE INDEX idx_whatsapp_templates_status ON whatsapp_templates(approval_status);

-- ── HMO directory (Nigeria — required, not optional) ─────────────────────────
-- Over 50 HMOs require electronic claims in Nigeria. Minimal directory to
-- support eligibility lookups during walk-in and standalone intake.
CREATE TABLE IF NOT EXISTS hmo_directory (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name                TEXT NOT NULL UNIQUE,
    short_code          TEXT,
    claims_api_url      TEXT,
    claims_api_type     TEXT DEFAULT 'manual' CHECK (claims_api_type IN ('manual', 'api', 'edi')),
    active              BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Seed common Nigerian HMOs referenced by hospital staff during interviews
INSERT INTO hmo_directory (name, short_code, claims_api_type) VALUES
    ('NHIS', 'NHIS', 'manual'),
    ('Hygeia HMO', 'HYG', 'manual'),
    ('AXA Mansard Health', 'AXA', 'manual'),
    ('Avon HMO', 'AVON', 'manual'),
    ('Reliance HMO', 'REL', 'manual'),
    ('Total Health Trust', 'THT', 'manual')
ON CONFLICT (name) DO NOTHING;

-- ── Updated_at triggers for new tables ───────────────────────────────────────
CREATE TRIGGER walkin_visits_updated_at BEFORE UPDATE ON walkin_visits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER standalone_patients_updated_at BEFORE UPDATE ON standalone_patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER standalone_appointments_updated_at BEFORE UPDATE ON standalone_appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ── HMO claims (added alongside hmo_directory above) ─────────────────────────
CREATE TABLE IF NOT EXISTS hmo_claims (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id           TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_id          TEXT,
    hmo_id              TEXT REFERENCES hmo_directory(id),
    visit_id            TEXT,
    diagnosis_code      TEXT NOT NULL,
    service_codes       TEXT[] NOT NULL,
    amount_ngn          NUMERIC(12,2) NOT NULL,
    amount_approved_ngn NUMERIC(12,2),
    status              TEXT DEFAULT 'submitted' CHECK (status IN ('submitted', 'approved', 'rejected', 'paid')),
    submitted_at        TIMESTAMPTZ DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ
);

ALTER TABLE hmo_claims ENABLE ROW LEVEL SECURITY;

CREATE POLICY hmo_claims_clinic_isolation ON hmo_claims
    USING (clinic_id IN (
        SELECT id FROM clinics
        WHERE clerk_org_id = current_setting('app.clerk_org_id', true)
    ));

CREATE INDEX idx_hmo_claims_clinic ON hmo_claims(clinic_id, status);

-- ── Patient payments (cash, POS, bank transfer, Paystack, Flutterwave) ──────
CREATE TABLE IF NOT EXISTS patient_payments (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id           TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_id          TEXT,
    visit_id            TEXT,
    method              TEXT NOT NULL CHECK (method IN ('cash', 'pos', 'bank_transfer', 'paystack', 'flutterwave', 'card', 'insurance')),
    amount_ngn          NUMERIC(12,2),
    amount_usd          NUMERIC(12,2),
    received_by         TEXT,
    pos_terminal_id     TEXT,
    provider_reference  TEXT,
    status              TEXT DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    recorded_at         TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE patient_payments ENABLE ROW LEVEL SECURITY;

CREATE POLICY patient_payments_clinic_isolation ON patient_payments
    USING (clinic_id IN (
        SELECT id FROM clinics
        WHERE clerk_org_id = current_setting('app.clerk_org_id', true)
    ));

CREATE INDEX idx_patient_payments_clinic ON patient_payments(clinic_id, recorded_at DESC);
