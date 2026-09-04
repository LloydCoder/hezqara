-- HEZQARA tenant boundary hardening.
-- The API derives app.clerk_org_id from a verified Clerk Organization and sets it
-- LOCAL for each transaction. FORCE RLS prevents the table owner from bypassing it.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['patients','appointments','calls','insurance','prior_auth','refills','referrals','recalls','documents','audit_log'] LOOP
    IF to_regclass('public.'||t) IS NOT NULL THEN
      EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
      EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY', t);
      EXECUTE format('DROP POLICY IF EXISTS hezqara_tenant_select ON public.%I', t);
      EXECUTE format('DROP POLICY IF EXISTS hezqara_tenant_insert ON public.%I', t);
      EXECUTE format('DROP POLICY IF EXISTS hezqara_tenant_update ON public.%I', t);
      EXECUTE format('DROP POLICY IF EXISTS hezqara_tenant_delete ON public.%I', t);
      EXECUTE format('CREATE POLICY hezqara_tenant_select ON public.%I FOR SELECT TO authenticated USING (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))', t);
      EXECUTE format('CREATE POLICY hezqara_tenant_insert ON public.%I FOR INSERT TO authenticated WITH CHECK (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))', t);
      EXECUTE format('CREATE POLICY hezqara_tenant_update ON public.%I FOR UPDATE TO authenticated USING (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true))) WITH CHECK (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))', t);
      EXECUTE format('CREATE POLICY hezqara_tenant_delete ON public.%I FOR DELETE TO authenticated USING (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))', t);
    END IF;
  END LOOP;
END $$;
ALTER TABLE IF EXISTS public.clinics ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.clinics FORCE ROW LEVEL SECURITY;
