-- Phase 3 audit contract hardening and role grants.
ALTER TABLE public.audit_log ADD COLUMN IF NOT EXISTS actor_id TEXT;
ALTER TABLE public.audit_log ADD COLUMN IF NOT EXISTS resource_type TEXT;
ALTER TABLE public.audit_log ADD COLUMN IF NOT EXISTS resource_id TEXT;
ALTER TABLE public.audit_log ADD COLUMN IF NOT EXISTS request_id TEXT;
ALTER TABLE public.audit_log ADD COLUMN IF NOT EXISTS outcome TEXT;
ALTER TABLE public.audit_log ADD COLUMN IF NOT EXISTS source TEXT;
CREATE INDEX IF NOT EXISTS idx_audit_request ON public.audit_log(request_id) WHERE request_id IS NOT NULL;
GRANT USAGE, SELECT ON SEQUENCE public.audit_log_id_seq TO authenticated;

-- Remove legacy broad policies before the explicit authenticated policies are applied.
DROP POLICY IF EXISTS clinics_isolation ON public.clinics;
DROP POLICY IF EXISTS patients_clinic_isolation ON public.patients;
DROP POLICY IF EXISTS appointments_clinic_isolation ON public.appointments;
DROP POLICY IF EXISTS hezqara_tenant_select ON public.clinics;
DROP POLICY IF EXISTS hezqara_tenant_insert ON public.clinics;
DROP POLICY IF EXISTS hezqara_tenant_update ON public.clinics;
DROP POLICY IF EXISTS hezqara_tenant_delete ON public.clinics;

CREATE POLICY hezqara_clinics_select ON public.clinics FOR SELECT TO authenticated USING (clerk_org_id=current_setting('app.clerk_org_id',true));
CREATE POLICY hezqara_clinics_insert ON public.clinics FOR INSERT TO authenticated WITH CHECK (clerk_org_id=current_setting('app.clerk_org_id',true));
CREATE POLICY hezqara_clinics_update ON public.clinics FOR UPDATE TO authenticated USING (clerk_org_id=current_setting('app.clerk_org_id',true)) WITH CHECK (clerk_org_id=current_setting('app.clerk_org_id',true));

DO $$ DECLARE t text; BEGIN
  FOREACH t IN ARRAY ARRAY['patients','appointments','calls','insurance','prior_auth','refills','referrals','recalls','documents','walkin_visits','walkin_qr_codes','standalone_patients','standalone_appointments'] LOOP
    IF to_regclass('public.'||t) IS NOT NULL THEN
      EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', 'patients_clinic_isolation', t);
      EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', 'appointments_clinic_isolation', t);
    END IF;
  END LOOP;
END $$;
