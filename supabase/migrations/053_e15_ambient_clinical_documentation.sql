-- Migration 053: E15 ambient clinical documentation.

CREATE UNIQUE INDEX IF NOT EXISTS appointments_clinic_id_uidx ON appointments(clinic_id,id);

CREATE TABLE IF NOT EXISTS scribe_encounters (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_id TEXT NOT NULL,
    appointment_id TEXT,
    clinician_id TEXT,
    consent_status TEXT NOT NULL DEFAULT 'unknown'
      CHECK(consent_status IN ('unknown','obtained','declined','not_required')),
    status TEXT NOT NULL DEFAULT 'created'
      CHECK(status IN ('created','recording','transcribing','draft','review','approved','committed','rejected','failed')),
    audio_ref TEXT,
    audio_retention_until DATE,
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT scribe_encounters_patient_tenant_fk
      FOREIGN KEY (clinic_id,patient_id) REFERENCES patients(clinic_id,id),
    CONSTRAINT scribe_encounters_appointment_tenant_fk
      FOREIGN KEY (clinic_id,appointment_id) REFERENCES appointments(clinic_id,id)
);

CREATE UNIQUE INDEX IF NOT EXISTS scribe_encounters_clinic_id_uidx ON scribe_encounters(clinic_id,id);

CREATE TABLE IF NOT EXISTS scribe_transcripts (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    encounter_id TEXT NOT NULL,
    provider_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    language_code TEXT,
    transcript_text TEXT NOT NULL,
    segments JSONB NOT NULL DEFAULT '[]'::jsonb,
    provider_request_id TEXT,
    provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT scribe_transcripts_encounter_tenant_fk
      FOREIGN KEY (clinic_id,encounter_id) REFERENCES scribe_encounters(clinic_id,id)
);

CREATE TABLE IF NOT EXISTS scribe_notes (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    encounter_id TEXT NOT NULL,
    transcript_id TEXT,
    note_type TEXT NOT NULL DEFAULT 'clinical_note',
    template_version TEXT NOT NULL DEFAULT 'e15.v1',
    model_version TEXT,
    note_text TEXT NOT NULL,
    structured_note JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'draft'
      CHECK(status IN ('draft','review','approved','rejected','committed')),
    clinician_id TEXT,
    approved_at TIMESTAMPTZ,
    committed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT scribe_notes_encounter_tenant_fk
      FOREIGN KEY (clinic_id,encounter_id) REFERENCES scribe_encounters(clinic_id,id),
    CONSTRAINT scribe_notes_transcript_tenant_fk
      FOREIGN KEY (clinic_id,transcript_id) REFERENCES scribe_transcripts(clinic_id,id)
);

CREATE UNIQUE INDEX IF NOT EXISTS scribe_notes_clinic_id_uidx ON scribe_notes(clinic_id,id);

CREATE TABLE IF NOT EXISTS scribe_note_provenance (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    note_id TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK(source_type IN ('transcript','clinician_edit','template','model')),
    source_id TEXT,
    source_ref TEXT,
    excerpt TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT scribe_note_provenance_note_tenant_fk
      FOREIGN KEY (clinic_id,note_id) REFERENCES scribe_notes(clinic_id,id)
);

CREATE TABLE IF NOT EXISTS scribe_events (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    encounter_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    actor TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT scribe_events_encounter_tenant_fk
      FOREIGN KEY (clinic_id,encounter_id) REFERENCES scribe_encounters(clinic_id,id)
);

ALTER TABLE scribe_encounters ENABLE ROW LEVEL SECURITY;
ALTER TABLE scribe_encounters FORCE ROW LEVEL SECURITY;
CREATE POLICY scribe_encounters_isolation ON scribe_encounters
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

ALTER TABLE scribe_transcripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE scribe_transcripts FORCE ROW LEVEL SECURITY;
CREATE POLICY scribe_transcripts_isolation ON scribe_transcripts
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

ALTER TABLE scribe_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE scribe_notes FORCE ROW LEVEL SECURITY;
CREATE POLICY scribe_notes_isolation ON scribe_notes
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

ALTER TABLE scribe_note_provenance ENABLE ROW LEVEL SECURITY;
ALTER TABLE scribe_note_provenance FORCE ROW LEVEL SECURITY;
CREATE POLICY scribe_note_provenance_isolation ON scribe_note_provenance
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

ALTER TABLE scribe_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE scribe_events FORCE ROW LEVEL SECURITY;
CREATE POLICY scribe_events_isolation ON scribe_events
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

GRANT SELECT,INSERT,UPDATE,DELETE
ON scribe_encounters,scribe_transcripts,scribe_notes,scribe_note_provenance,scribe_events
TO authenticated;

CREATE INDEX IF NOT EXISTS idx_scribe_encounters_patient ON scribe_encounters(clinic_id,patient_id,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scribe_encounters_status ON scribe_encounters(clinic_id,status,updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_scribe_transcripts_encounter ON scribe_transcripts(clinic_id,encounter_id,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scribe_notes_encounter ON scribe_notes(clinic_id,encounter_id,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scribe_provenance_note ON scribe_note_provenance(clinic_id,note_id,created_at);
CREATE INDEX IF NOT EXISTS idx_scribe_events_encounter ON scribe_events(clinic_id,encounter_id,created_at DESC);
