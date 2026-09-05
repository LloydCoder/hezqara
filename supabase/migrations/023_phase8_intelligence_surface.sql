-- Phase 8 intelligence surface: indexes only; analytics remain derived and tenant-scoped.
CREATE INDEX IF NOT EXISTS idx_audit_clinic_created_action ON audit_log(clinic_id,created_at,action);
CREATE INDEX IF NOT EXISTS idx_audit_clinic_created_agent ON audit_log(clinic_id,created_at,agent_type);
CREATE INDEX IF NOT EXISTS idx_claims_clinic_created_status ON claims(clinic_id,created_at,status);
CREATE INDEX IF NOT EXISTS idx_billing_charges_clinic_created_status ON billing_charges(clinic_id,created_at,status);
CREATE INDEX IF NOT EXISTS idx_billing_payments_clinic_created_status ON billing_payments(clinic_id,created_at,status);
CREATE INDEX IF NOT EXISTS idx_eligibility_clinic_responded_status ON eligibility_requests(clinic_id,responded_at,status);
CREATE INDEX IF NOT EXISTS idx_authorizations_clinic_response_status ON authorizations(clinic_id,response_at,status);
