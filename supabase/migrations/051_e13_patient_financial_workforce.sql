-- Migration 051: E13 patient financial workforce.

CREATE TABLE IF NOT EXISTS patient_statements (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    account_id TEXT NOT NULL,
    patient_id TEXT NOT NULL,
    statement_number TEXT NOT NULL,
    amount_due NUMERIC(12,2) NOT NULL CHECK(amount_due >= 0),
    due_date DATE,
    status TEXT NOT NULL DEFAULT 'draft'
      CHECK(status IN ('draft','issued','paid','void','collections')),
    delivery_channel TEXT NOT NULL DEFAULT 'portal'
      CHECK(delivery_channel IN ('portal','email','sms','mail','staff')),
    issued_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(clinic_id,statement_number),
    CONSTRAINT patient_statements_account_tenant_fk
      FOREIGN KEY (clinic_id,account_id) REFERENCES billing_accounts(clinic_id,id),
    CONSTRAINT patient_statements_patient_tenant_fk
      FOREIGN KEY (clinic_id,patient_id) REFERENCES patients(clinic_id,id)
);

CREATE TABLE IF NOT EXISTS cost_estimates (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_id TEXT NOT NULL,
    account_id TEXT,
    coverage_id TEXT,
    services JSONB NOT NULL DEFAULT '[]'::jsonb,
    estimated_charges NUMERIC(12,2) NOT NULL CHECK(estimated_charges >= 0),
    estimated_payer_responsibility NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK(estimated_payer_responsibility >= 0),
    estimated_patient_responsibility NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK(estimated_patient_responsibility >= 0),
    assumptions JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL DEFAULT 'estimate'
      CHECK(status IN ('estimate','expired','superseded')),
    expires_at TIMESTAMPTZ,
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT cost_estimates_patient_tenant_fk
      FOREIGN KEY (clinic_id,patient_id) REFERENCES patients(clinic_id,id)
);

CREATE TABLE IF NOT EXISTS payment_plans (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    account_id TEXT NOT NULL,
    patient_id TEXT NOT NULL,
    total_amount NUMERIC(12,2) NOT NULL CHECK(total_amount >= 0),
    remaining_amount NUMERIC(12,2) NOT NULL CHECK(remaining_amount >= 0),
    installment_amount NUMERIC(12,2) NOT NULL CHECK(installment_amount > 0),
    frequency TEXT NOT NULL CHECK(frequency IN ('weekly','biweekly','monthly')),
    next_due_date DATE,
    status TEXT NOT NULL DEFAULT 'active'
      CHECK(status IN ('active','paused','completed','cancelled','defaulted')),
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT payment_plans_account_tenant_fk
      FOREIGN KEY (clinic_id,account_id) REFERENCES billing_accounts(clinic_id,id),
    CONSTRAINT payment_plans_patient_tenant_fk
      FOREIGN KEY (clinic_id,patient_id) REFERENCES patients(clinic_id,id)
);

CREATE TABLE IF NOT EXISTS financial_assistance_cases (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    account_id TEXT NOT NULL,
    patient_id TEXT NOT NULL,
    requested_amount NUMERIC(12,2) NOT NULL CHECK(requested_amount >= 0),
    approved_amount NUMERIC(12,2),
    reason TEXT,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL DEFAULT 'requested'
      CHECK(status IN ('requested','in_review','approved','denied','cancelled')),
    reviewer_id TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT financial_assistance_account_tenant_fk
      FOREIGN KEY (clinic_id,account_id) REFERENCES billing_accounts(clinic_id,id),
    CONSTRAINT financial_assistance_patient_tenant_fk
      FOREIGN KEY (clinic_id,patient_id) REFERENCES patients(clinic_id,id)
);

CREATE TABLE IF NOT EXISTS payment_reconciliations (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    payment_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    applied_amount NUMERIC(12,2) NOT NULL CHECK(applied_amount > 0),
    external_reference TEXT,
    status TEXT NOT NULL DEFAULT 'reconciled'
      CHECK(status IN ('reconciled','exception','reversed')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT payment_reconciliations_payment_tenant_fk
      FOREIGN KEY (clinic_id,payment_id) REFERENCES billing_payments(clinic_id,id),
    CONSTRAINT payment_reconciliations_account_tenant_fk
      FOREIGN KEY (clinic_id,account_id) REFERENCES billing_accounts(clinic_id,id)
);

ALTER TABLE patient_statements ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_statements FORCE ROW LEVEL SECURITY;
CREATE POLICY patient_statements_isolation ON patient_statements
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

ALTER TABLE cost_estimates ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_estimates FORCE ROW LEVEL SECURITY;
CREATE POLICY cost_estimates_isolation ON cost_estimates
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

ALTER TABLE payment_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_plans FORCE ROW LEVEL SECURITY;
CREATE POLICY payment_plans_isolation ON payment_plans
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

ALTER TABLE financial_assistance_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE financial_assistance_cases FORCE ROW LEVEL SECURITY;
CREATE POLICY financial_assistance_cases_isolation ON financial_assistance_cases
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

ALTER TABLE payment_reconciliations ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_reconciliations FORCE ROW LEVEL SECURITY;
CREATE POLICY payment_reconciliations_isolation ON payment_reconciliations
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

GRANT SELECT,INSERT,UPDATE,DELETE
ON billing_accounts,billing_charges,billing_payments,patient_statements,cost_estimates,payment_plans,
   financial_assistance_cases,payment_reconciliations
TO authenticated;

CREATE INDEX IF NOT EXISTS idx_e13_statements_account ON patient_statements(clinic_id,account_id,status);
CREATE INDEX IF NOT EXISTS idx_e13_estimates_patient ON cost_estimates(clinic_id,patient_id,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_e13_plans_account ON payment_plans(clinic_id,account_id,status);
CREATE INDEX IF NOT EXISTS idx_e13_assistance_account ON financial_assistance_cases(clinic_id,account_id,status);
CREATE INDEX IF NOT EXISTS idx_e13_reconciliation_payment ON payment_reconciliations(clinic_id,payment_id);
