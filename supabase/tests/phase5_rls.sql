\set ON_ERROR_STOP on
INSERT INTO clinics(id,name,clerk_org_id) VALUES ('phase5-a','Phase5 A','org_phase5_a'),('phase5-b','Phase5 B','org_phase5_b') ON CONFLICT (id) DO NOTHING;
INSERT INTO patients(id,clinic_id,first_name,last_name,email) VALUES ('phase5-p-a','phase5-a','A','Patient','a@example.invalid'),('phase5-p-b','phase5-b','B','Patient','b@example.invalid') ON CONFLICT (id) DO NOTHING;
SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','org_phase5_a',false);
INSERT INTO patient_communication_preferences(clinic_id,patient_id) VALUES ('phase5-a','phase5-p-a') ON CONFLICT DO NOTHING;
DO $$ BEGIN IF (SELECT count(*) FROM patient_communication_preferences WHERE patient_id='phase5-p-b') <> 0 THEN RAISE EXCEPTION 'cross-tenant preference leaked'; END IF; END $$;
DO $$ BEGIN IF EXISTS (SELECT 1 FROM communications WHERE clinic_id='phase5-b') THEN RAISE EXCEPTION 'cross-tenant communication leaked'; END IF; END $$;
RESET ROLE;
SELECT 'phase5_rls_ok' AS result;
