-- Phase 6: healthcare administrative domain engine.
-- New tables are tenant-owned and isolated with RLS. Existing historical migrations are untouched.

CREATE TABLE IF NOT EXISTS patient_coverages (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 patient_id TEXT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
 payer_name TEXT NOT NULL, plan_name TEXT, member_id TEXT NOT NULL, group_number TEXT,
 subscriber_name TEXT, subscriber_relationship TEXT,
 effective_date DATE, termination_date DATE,
 priority INTEGER NOT NULL DEFAULT 1 CHECK (priority > 0),
 status TEXT NOT NULL DEFAULT 'unknown' CHECK (status IN ('unknown','active','inactive','expired')),
 verification_state TEXT NOT NULL DEFAULT 'pending_verification' CHECK (verification_state IN ('pending_verification','verified','verification_failed')),
 last_verified_at TIMESTAMPTZ, source TEXT NOT NULL DEFAULT 'manual', created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE (clinic_id, patient_id, member_id, priority)
);
CREATE TABLE IF NOT EXISTS eligibility_requests (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 patient_id TEXT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
 coverage_id TEXT REFERENCES patient_coverages(id) ON DELETE SET NULL,
 payer_name TEXT NOT NULL, service_code TEXT, status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','submitted','eligible','ineligible','additional_information_required','unavailable','provider_error','failed')),
 provider TEXT NOT NULL DEFAULT 'not_configured', provider_reference TEXT, response JSONB NOT NULL DEFAULT '{}'::jsonb,
 idempotency_key TEXT NOT NULL, correlation_id TEXT, requested_at TIMESTAMPTZ NOT NULL DEFAULT now(), responded_at TIMESTAMPTZ,
 UNIQUE (clinic_id,idempotency_key)
);
CREATE TABLE IF NOT EXISTS billing_accounts (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 patient_id TEXT NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
 status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','closed','collections','voided')),
 currency CHAR(3) NOT NULL DEFAULT 'USD', created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(clinic_id,patient_id)
);
CREATE TABLE IF NOT EXISTS billing_charges (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 account_id TEXT NOT NULL REFERENCES billing_accounts(id) ON DELETE RESTRICT,
 patient_id TEXT NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
 service_date DATE NOT NULL, description TEXT NOT NULL, amount NUMERIC(12,2) NOT NULL CHECK(amount >= 0), payer_responsibility NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK(payer_responsibility >= 0), patient_responsibility NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK(patient_responsibility >= 0), status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','submitted','paid','denied','voided','closed')), source TEXT NOT NULL DEFAULT 'manual', created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), CHECK(payer_responsibility + patient_responsibility <= amount)
);
CREATE TABLE IF NOT EXISTS billing_payments (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 account_id TEXT NOT NULL REFERENCES billing_accounts(id) ON DELETE RESTRICT,
 amount NUMERIC(12,2) NOT NULL CHECK(amount > 0), status TEXT NOT NULL CHECK(status IN ('pending','authorized','paid','failed','refunded','voided')),
 provider TEXT, provider_reference TEXT, idempotency_key TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(clinic_id,idempotency_key)
);
CREATE TABLE IF NOT EXISTS claims (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 patient_id TEXT NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
 coverage_id TEXT REFERENCES patient_coverages(id) ON DELETE SET NULL,
 payer_name TEXT NOT NULL, billed_amount NUMERIC(12,2) NOT NULL CHECK(billed_amount >= 0), expected_amount NUMERIC(12,2) CHECK(expected_amount >= 0), paid_amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK(paid_amount >= 0), patient_responsibility NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK(patient_responsibility >= 0), status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','ready','submitted','accepted','rejected','pending','paid','partially_paid','denied','appealed','closed')), payer_reference TEXT, submission_reference TEXT, rejection_reason TEXT, denial_reason TEXT, submitted_at TIMESTAMPTZ, responded_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS claim_lines (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 claim_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
 service_date DATE NOT NULL, service_code TEXT NOT NULL, description TEXT, amount NUMERIC(12,2) NOT NULL CHECK(amount >= 0), units NUMERIC(8,2) NOT NULL DEFAULT 1 CHECK(units > 0), created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS claim_adjudications (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 claim_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
 payer_reference TEXT, billed_amount NUMERIC(12,2) NOT NULL CHECK(billed_amount >= 0), allowed_amount NUMERIC(12,2), paid_amount NUMERIC(12,2) NOT NULL DEFAULT 0, deductible NUMERIC(12,2) NOT NULL DEFAULT 0, coinsurance NUMERIC(12,2) NOT NULL DEFAULT 0, copay NUMERIC(12,2) NOT NULL DEFAULT 0, patient_responsibility NUMERIC(12,2) NOT NULL DEFAULT 0, adjustment_reason TEXT, received_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS ar_work_items (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 claim_id TEXT REFERENCES claims(id) ON DELETE SET NULL,
 patient_id TEXT REFERENCES patients(id) ON DELETE SET NULL,
 responsibility TEXT NOT NULL CHECK(responsibility IN ('payer','patient')),
 amount NUMERIC(12,2) NOT NULL CHECK(amount >= 0), aging_bucket TEXT NOT NULL DEFAULT '0_30' CHECK(aging_bucket IN ('0_30','31_60','61_90','91_120','120_plus')),
 status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','assigned','follow_up','escalated','resolved','closed')),
 owner_id TEXT, next_follow_up_at TIMESTAMPTZ, notes TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS denials (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 claim_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
 denial_code TEXT, category TEXT NOT NULL DEFAULT 'unknown', payer_name TEXT NOT NULL, amount NUMERIC(12,2) NOT NULL CHECK(amount >= 0), received_at TIMESTAMPTZ NOT NULL DEFAULT now(), deadline_at TIMESTAMPTZ, status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','assigned','in_review','appeal_ready','appealed','resolved','closed')), owner_id TEXT, recommended_action TEXT, appeal_state TEXT NOT NULL DEFAULT 'not_started' CHECK(appeal_state IN ('not_started','draft','ready','submitted','accepted','denied','closed')), created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS authorizations (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 patient_id TEXT NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
 coverage_id TEXT REFERENCES patient_coverages(id) ON DELETE SET NULL,
 payer_name TEXT NOT NULL, service_code TEXT NOT NULL, requested_date DATE, documentation_required TEXT[] NOT NULL DEFAULT '{}', status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','ready_for_review','approved_for_submission','submitted','pending','additional_information_required','approved','denied','expired','cancelled')), payer_reference TEXT, pending_reason TEXT, denial_reason TEXT, submitted_at TIMESTAMPTZ, response_at TIMESTAMPTZ, expires_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS referrals_v2 (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 patient_id TEXT NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
 referring_provider TEXT, receiving_provider TEXT, destination TEXT NOT NULL, service TEXT, documentation_required TEXT[] NOT NULL DEFAULT '{}', authorization_id TEXT REFERENCES authorizations(id) ON DELETE SET NULL, status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','pending_review','ready','sent','received','accepted','scheduled','completed','expired','cancelled')), expires_at TIMESTAMPTZ, last_follow_up_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS records_v2 (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 patient_id TEXT NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
 document_type TEXT NOT NULL, source TEXT NOT NULL, received_at TIMESTAMPTZ, status TEXT NOT NULL DEFAULT 'received' CHECK(status IN ('expected','received','indexed','missing','restricted','archived')), required BOOLEAN NOT NULL DEFAULT false, related_workflow_id TEXT, retention_until DATE, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_p6_coverages_patient ON patient_coverages(clinic_id,patient_id,priority);
CREATE INDEX IF NOT EXISTS idx_p6_eligibility_status ON eligibility_requests(clinic_id,status,requested_at DESC);
CREATE INDEX IF NOT EXISTS idx_p6_charges_account ON billing_charges(clinic_id,account_id,status);
CREATE INDEX IF NOT EXISTS idx_p6_payments_account ON billing_payments(clinic_id,account_id,status);
CREATE INDEX IF NOT EXISTS idx_p6_claims_status ON claims(clinic_id,status,updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_p6_claim_lines_claim ON claim_lines(clinic_id,claim_id);
CREATE INDEX IF NOT EXISTS idx_p6_adj_claim ON claim_adjudications(clinic_id,claim_id,received_at DESC);
CREATE INDEX IF NOT EXISTS idx_p6_ar_queue ON ar_work_items(clinic_id,status,aging_bucket,updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_p6_denials_queue ON denials(clinic_id,status,deadline_at);
CREATE INDEX IF NOT EXISTS idx_p6_auth_status ON authorizations(clinic_id,status,updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_p6_referrals_status ON referrals_v2(clinic_id,status,updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_p6_records_patient ON records_v2(clinic_id,patient_id,status);

DO $$ DECLARE t TEXT; BEGIN FOR t IN SELECT unnest(ARRAY['patient_coverages','eligibility_requests','billing_accounts','billing_charges','billing_payments','claims','claim_lines','claim_adjudications','ar_work_items','denials','authorizations','referrals_v2','records_v2']) LOOP EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t); EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t); EXECUTE format('DROP POLICY IF EXISTS phase6_tenant_select ON %I',t); EXECUTE format('DROP POLICY IF EXISTS phase6_tenant_write ON %I',t); EXECUTE format('CREATE POLICY phase6_tenant_select ON %I FOR SELECT TO authenticated USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))',t); EXECUTE format('CREATE POLICY phase6_tenant_write ON %I FOR ALL TO authenticated USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true))) WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))',t); EXECUTE format('REVOKE ALL ON %I FROM anon',t); EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON %I TO authenticated',t); END LOOP; END $$;
