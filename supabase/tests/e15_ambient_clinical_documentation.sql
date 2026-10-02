-- E15 database proof: ambient documentation tenant isolation and lifecycle persistence.
BEGIN;

INSERT INTO clinics(id,name,clerk_org_id) VALUES
 ('ci-e15-a','CI E15 A','ci_e15_org_a'),
 ('ci-e15-b','CI E15 B','ci_e15_org_b')
ON CONFLICT (id) DO NOTHING;

INSERT INTO patients(id,clinic_id,first_name,last_name)
VALUES ('ci-e15-patient-a','ci-e15-a','E15','Patient')
ON CONFLICT (id) DO NOTHING;

INSERT INTO scribe_encounters(id,clinic_id,patient_id,clinician_id,consent_status,status)
VALUES ('ci-e15-enc-a','ci-e15-a','ci-e15-patient-a','clinician-a','obtained','review')
ON CONFLICT (id) DO NOTHING;

INSERT INTO scribe_transcripts(id,clinic_id,encounter_id,provider_name,model_version,transcript_text)
VALUES ('ci-e15-transcript-a','ci-e15-a','ci-e15-enc-a','test-provider','test-v1','Synthetic clinical conversation.')
ON CONFLICT (id) DO NOTHING;

INSERT INTO scribe_notes(id,clinic_id,encounter_id,transcript_id,note_text,status,clinician_id)
VALUES ('ci-e15-note-a','ci-e15-a','ci-e15-enc-a','ci-e15-transcript-a','Synthetic draft.','review','clinician-a')
ON CONFLICT (id) DO NOTHING;

INSERT INTO scribe_note_provenance(id,clinic_id,note_id,source_type,source_id,source_ref)
VALUES ('ci-e15-prov-a','ci-e15-a','ci-e15-note-a','transcript','ci-e15-transcript-a','synthetic')
ON CONFLICT (id) DO NOTHING;

SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','ci_e15_org_a',false);

DO 'BEGIN
  IF NOT EXISTS (SELECT 1 FROM scribe_notes WHERE id=''ci-e15-note-a'') THEN
    RAISE EXCEPTION ''tenant A cannot read its own scribe note'';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM scribe_note_provenance WHERE id=''ci-e15-prov-a'') THEN
    RAISE EXCEPTION ''tenant A cannot read its own provenance'';
  END IF;
END';

SELECT set_config('app.clerk_org_id','ci_e15_org_b',false);

DO 'BEGIN
  IF EXISTS (SELECT 1 FROM scribe_notes WHERE id=''ci-e15-note-a'') THEN
    RAISE EXCEPTION ''cross-tenant scribe note read'';
  END IF;
  IF EXISTS (SELECT 1 FROM scribe_transcripts WHERE id=''ci-e15-transcript-a'') THEN
    RAISE EXCEPTION ''cross-tenant transcript read'';
  END IF;
END';

RESET ROLE;
ROLLBACK;
