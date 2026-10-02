-- E14 database proof: document intake/routing and referral event tenant isolation.
BEGIN;

INSERT INTO clinics(id,name,clerk_org_id) VALUES
 ('ci-e14-a','CI E14 A','ci_e14_org_a'),
 ('ci-e14-b','CI E14 B','ci_e14_org_b')
ON CONFLICT (id) DO NOTHING;

INSERT INTO patients(id,clinic_id,first_name,last_name)
VALUES ('ci-e14-patient-a','ci-e14-a','E14','Patient')
ON CONFLICT (id) DO NOTHING;

INSERT INTO document_intake_items(id,clinic_id,patient_id,source,filename,status)
VALUES ('ci-e14-intake-a','ci-e14-a','ci-e14-patient-a','fax','referral.pdf','matched')
ON CONFLICT (id) DO NOTHING;

INSERT INTO referrals_v2(id,clinic_id,patient_id,destination,service,status)
VALUES ('ci-e14-referral-a','ci-e14-a','ci-e14-patient-a','Specialist A','consult','draft')
ON CONFLICT (id) DO NOTHING;

INSERT INTO document_routes(id,clinic_id,intake_id,target_type,target_id,status)
VALUES ('ci-e14-route-a','ci-e14-a','ci-e14-intake-a','referral','ci-e14-referral-a','routed')
ON CONFLICT (id) DO NOTHING;

INSERT INTO referral_events(id,clinic_id,referral_id,to_status,actor)
VALUES ('ci-e14-event-a','ci-e14-a','ci-e14-referral-a','draft','ci-e14-test')
ON CONFLICT (id) DO NOTHING;

SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','ci_e14_org_a',false);

DO 'BEGIN
  IF NOT EXISTS (SELECT 1 FROM document_intake_items WHERE id=''ci-e14-intake-a'') THEN
    RAISE EXCEPTION ''tenant A cannot read its own intake'';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM referral_events WHERE id=''ci-e14-event-a'') THEN
    RAISE EXCEPTION ''tenant A cannot read its own referral event'';
  END IF;
END';

SELECT set_config('app.clerk_org_id','ci_e14_org_b',false);

DO 'BEGIN
  IF EXISTS (SELECT 1 FROM document_intake_items WHERE id=''ci-e14-intake-a'') THEN
    RAISE EXCEPTION ''cross-tenant intake read'';
  END IF;
  IF EXISTS (SELECT 1 FROM document_routes WHERE id=''ci-e14-route-a'') THEN
    RAISE EXCEPTION ''cross-tenant route read'';
  END IF;
END';

RESET ROLE;
ROLLBACK;
