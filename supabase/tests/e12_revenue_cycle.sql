-- E12 database proof: claim, scrub, denial and appeal tenant isolation.
BEGIN;

INSERT INTO clinics(id,name,clerk_org_id) VALUES
 ('ci-e12-a','CI E12 A','ci_e12_org_a'),
 ('ci-e12-b','CI E12 B','ci_e12_org_b')
ON CONFLICT (id) DO NOTHING;

INSERT INTO patients(id,clinic_id,first_name,last_name)
VALUES ('ci-e12-patient-a','ci-e12-a','E12','Patient')
ON CONFLICT (id) DO NOTHING;

INSERT INTO claims(id,clinic_id,patient_id,payer_name,billed_amount,status,creation_idempotency_key)
VALUES ('ci-e12-claim-a','ci-e12-a','ci-e12-patient-a','Payer A',100,'draft','ci-e12-claim-key')
ON CONFLICT (id) DO NOTHING;

INSERT INTO claim_lines(id,clinic_id,claim_id,service_date,service_code,amount,units)
VALUES ('ci-e12-line-a','ci-e12-a','ci-e12-claim-a','2031-01-01','PROC-1',100,1)
ON CONFLICT (id) DO NOTHING;

INSERT INTO denials(id,clinic_id,claim_id,payer_name,amount,category)
VALUES ('ci-e12-denial-a','ci-e12-a','ci-e12-claim-a','Payer A',100,'authorization')
ON CONFLICT (id) DO NOTHING;

INSERT INTO claim_scrub_results(id,clinic_id,claim_id,status)
VALUES ('ci-e12-scrub-a','ci-e12-a','ci-e12-claim-a','passed')
ON CONFLICT (id) DO NOTHING;

SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','ci_e12_org_a',false);

DO 'BEGIN
  IF NOT EXISTS (SELECT 1 FROM claims WHERE id=''ci-e12-claim-a'') THEN
    RAISE EXCEPTION ''tenant A cannot read its own claim'';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM claim_scrub_results WHERE id=''ci-e12-scrub-a'') THEN
    RAISE EXCEPTION ''tenant A cannot read its own scrub result'';
  END IF;
END';

SELECT set_config('app.clerk_org_id','ci_e12_org_b',false);

DO 'BEGIN
  IF EXISTS (SELECT 1 FROM claims WHERE id=''ci-e12-claim-a'') THEN
    RAISE EXCEPTION ''cross-tenant claim read'';
  END IF;
  IF EXISTS (SELECT 1 FROM denial_appeals WHERE denial_id=''ci-e12-denial-a'') THEN
    RAISE EXCEPTION ''cross-tenant appeal read'';
  END IF;
END';

RESET ROLE;
ROLLBACK;
