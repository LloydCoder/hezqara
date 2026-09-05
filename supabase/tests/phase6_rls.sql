-- Phase 6 RLS contract. Run as database owner against the CI database.
INSERT INTO clinics(id,name,clerk_org_id) VALUES ('p6-a','Phase6 A','p6_org_a'),('p6-b','Phase6 B','p6_org_b') ON CONFLICT (id) DO NOTHING;
INSERT INTO patients(id,clinic_id,first_name,last_name) VALUES ('p6-patient-a','p6-a','A','Patient'),('p6-patient-b','p6-b','B','Patient') ON CONFLICT (id) DO NOTHING;
INSERT INTO patient_coverages(clinic_id,patient_id,payer_name,member_id) VALUES ('p6-a','p6-patient-a','Test Payer','A-MEMBER'),('p6-b','p6-patient-b','Other Payer','B-MEMBER') ON CONFLICT DO NOTHING;
INSERT INTO billing_accounts(id,clinic_id,patient_id) VALUES ('p6-account-a','p6-a','p6-patient-a'),('p6-account-b','p6-b','p6-patient-b') ON CONFLICT (id) DO NOTHING;
INSERT INTO claims(id,clinic_id,patient_id,payer_name,billed_amount) VALUES ('p6-claim-a','p6-a','p6-patient-a','Test Payer',100),('p6-claim-b','p6-b','p6-patient-b','Other Payer',200) ON CONFLICT (id) DO NOTHING;
BEGIN;
SET LOCAL ROLE authenticated;
SELECT set_config('app.clerk_org_id','p6_org_a',true);
DO $$ DECLARE n integer; BEGIN
 SELECT count(*) INTO n FROM patient_coverages; IF n <> 1 THEN RAISE EXCEPTION 'coverage isolation failed: %',n; END IF;
 SELECT count(*) INTO n FROM claims; IF n <> 1 THEN RAISE EXCEPTION 'claim isolation failed: %',n; END IF;
 SELECT count(*) INTO n FROM billing_accounts; IF n <> 1 THEN RAISE EXCEPTION 'billing isolation failed: %',n; END IF;
 SELECT count(*) INTO n FROM authorizations; IF n <> 0 THEN RAISE EXCEPTION 'unexpected authorization visibility: %',n; END IF;
END $$;
ROLLBACK;
