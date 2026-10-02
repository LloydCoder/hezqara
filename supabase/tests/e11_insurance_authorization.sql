-- E11 database proof: insurance/authorization tenant isolation and lifecycle references.
BEGIN;

INSERT INTO clinics(id,name,clerk_org_id) VALUES
 ('ci-e11-a','CI E11 A','ci_e11_org_a'),
 ('ci-e11-b','CI E11 B','ci_e11_org_b')
ON CONFLICT (id) DO NOTHING;

INSERT INTO patients(id,clinic_id,first_name,last_name)
VALUES ('ci-e11-patient-a','ci-e11-a','E11','Patient')
ON CONFLICT (id) DO NOTHING;

INSERT INTO patient_coverages(id,clinic_id,patient_id,payer_name,member_id,priority)
VALUES ('ci-e11-coverage-a','ci-e11-a','ci-e11-patient-a','Payer A','MEM-A',1)
ON CONFLICT (id) DO NOTHING;

INSERT INTO authorizations(id,clinic_id,patient_id,coverage_id,payer_name,service_code,status,idempotency_key)
VALUES ('ci-e11-auth-a','ci-e11-a','ci-e11-patient-a','ci-e11-coverage-a','Payer A','PROC-1','draft','ci-e11-auth-key')
ON CONFLICT (id) DO NOTHING;

INSERT INTO coverage_benefits(id,clinic_id,coverage_id,service_code,category,in_network,copay)
VALUES ('ci-e11-benefit-a','ci-e11-a','ci-e11-coverage-a','PROC-1','office',true,25)
ON CONFLICT (id) DO NOTHING;

INSERT INTO authorization_documents(id,clinic_id,authorization_id,document_type,required,status)
VALUES ('ci-e11-doc-a','ci-e11-a','ci-e11-auth-a','clinical_note',true,'missing')
ON CONFLICT (id) DO NOTHING;

SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','ci_e11_org_a',false);

DO 'BEGIN
  IF NOT EXISTS (SELECT 1 FROM authorizations WHERE id=''ci-e11-auth-a'') THEN
    RAISE EXCEPTION ''tenant A cannot read its own authorization'';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM coverage_benefits WHERE id=''ci-e11-benefit-a'') THEN
    RAISE EXCEPTION ''tenant A cannot read its own benefit'';
  END IF;
END';


SELECT set_config('app.clerk_org_id','ci_e11_org_b',false);

DO 'BEGIN
  IF EXISTS (SELECT 1 FROM authorizations WHERE id=''ci-e11-auth-a'') THEN
    RAISE EXCEPTION ''cross-tenant authorization read'';
  END IF;
  IF EXISTS (SELECT 1 FROM authorization_documents WHERE id=''ci-e11-doc-a'') THEN
    RAISE EXCEPTION ''cross-tenant authorization document read'';
  END IF;
END';

RESET ROLE;
ROLLBACK;
