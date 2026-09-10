-- Phase 9 tenant policy hardening.
-- AI governance rows store internal clinics.id; app.clerk_org_id stores the
-- verified Clerk organization id. Resolve the tenant through clinics rather
-- than comparing two different identifier domains.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'ai_capabilities','ai_capability_versions','ai_evaluation_suites',
    'ai_evaluation_cases','ai_evaluation_runs','ai_evaluation_results',
    'ai_policy_versions','ai_policy_decisions','ai_execution_telemetry',
    'ai_failure_events','ai_approvals','ai_provider_health','ai_control_state'
  ] LOOP
    IF to_regclass('public.'||t) IS NOT NULL THEN
      EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', t||'_tenant', t);
      EXECUTE format(
        'CREATE POLICY %I ON public.%I TO authenticated USING (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true))) WITH CHECK (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))',
        t||'_tenant', t
      );
    END IF;
  END LOOP;
END $$;
