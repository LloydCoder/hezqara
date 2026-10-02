-- E13 database proof: patient financial tenant isolation and financial references.
BEGIN;

INSERT INTO clinics(id,name,clerk_org_id) VALUES
 ('ci-e13-a','CI E13 A','ci_e13_org_a'),
 ('ci-e13-b','CI E13 B','ci_e13_org_b')
ON CONFLICT (id) DO NOTHING;

INSERT INTO patients(id,clinic_id,first_name,last_name)
VALUES ('ci-e13-patient-a','ci-e13-a','E13','Patient')
ON CONFLICT (id) DO NOTHING;

INSERT INTO billing_accounts(id,clinic_id,patient_id,currency)
VALUES ('ci-e13-account-a','ci-e13-a','ci-e13-patient-a','USD')
ON CONFLICT (id) DO NOTHING;

INSERT INTO billing_payments(id,clinic_id,account_id,amount,status,idempotency_key)
VALUES ('ci-e13-payment-a','ci-e13-a','ci-e13-account-a',100,'paid','ci-e13-payment-key')
ON CONFLICT (id) DO NOTHING;

INSERT INTO patient_statements(id,clinic_id,account_id,patient_id,statement_number,amount_due,status)
VALUES ('ci-e13-statement-a','ci-e13-a','ci-e13-account-a','ci-e13-patient-a','CI-E13-STMT',100,'issued')
ON CONFLICT (id) DO NOTHING;

INSERT INTO payment_plans(id,clinic_id,account_id,patient_id,total_amount,remaining_amount,installment_amount,frequency)
VALUES ('ci-e13-plan-a','ci-e13-a','ci-e13-account-a','ci-e13-patient-a',100,100,25,'monthly')
ON CONFLICT (id) DO NOTHING;

INSERT INTO payment_reconciliations(id,clinic_id,payment_id,account_id,applied_amount)
VALUES ('ci-e13-recon-a','ci-e13-a','ci-e13-payment-a','ci-e13-account-a',100)
ON CONFLICT (id) DO NOTHING;

SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','ci_e13_org_a',false);

DO 'BEGIN
  IF NOT EXISTS (SELECT 1 FROM patient_statements WHERE id=''ci-e13-statement-a'') THEN
    RAISE EXCEPTION ''tenant A cannot read its own statement'';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM payment_reconciliations WHERE id=''ci-e13-recon-a'') THEN
    RAISE EXCEPTION ''tenant A cannot read its own reconciliation'';
  END IF;
END';

SELECT set_config('app.clerk_org_id','ci_e13_org_b',false);

DO 'BEGIN
  IF EXISTS (SELECT 1 FROM patient_statements WHERE id=''ci-e13-statement-a'') THEN
    RAISE EXCEPTION ''cross-tenant statement read'';
  END IF;
  IF EXISTS (SELECT 1 FROM payment_plans WHERE id=''ci-e13-plan-a'') THEN
    RAISE EXCEPTION ''cross-tenant payment plan read'';
  END IF;
END';

RESET ROLE;
ROLLBACK;
