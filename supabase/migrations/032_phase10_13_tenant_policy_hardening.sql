-- Phase 10-13 tenant policy hardening.
-- app.clerk_org_id is the verified Clerk organization id; tenant-owned rows
-- store internal clinics.id. Policies resolve the relationship server-side.

-- Growth leads must have their tenant column before the policy references it.
ALTER TABLE IF EXISTS public.growth_leads
  ADD COLUMN IF NOT EXISTS clinic_id TEXT REFERENCES public.clinics(id) ON DELETE CASCADE;
ALTER TABLE IF EXISTS public.growth_leads DROP CONSTRAINT IF EXISTS growth_leads_email_key;

DO $$
BEGIN
  IF to_regclass('public.growth_leads') IS NOT NULL THEN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='growth_leads_clinic_email_key' AND conrelid='public.growth_leads'::regclass) THEN
      ALTER TABLE public.growth_leads ADD CONSTRAINT growth_leads_clinic_email_key UNIQUE (clinic_id,email);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='growth_leads_clinic_id_id_key' AND conrelid='public.growth_leads'::regclass) THEN
      ALTER TABLE public.growth_leads ADD CONSTRAINT growth_leads_clinic_id_id_key UNIQUE (clinic_id,id);
    END IF;
    DROP POLICY IF EXISTS growth_leads_tenant ON public.growth_leads;
    CREATE POLICY growth_leads_tenant ON public.growth_leads TO authenticated
      USING (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
      WITH CHECK (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
    CREATE INDEX IF NOT EXISTS idx_growth_leads_clinic_email ON public.growth_leads(clinic_id,email);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.platform_settings') IS NOT NULL THEN
    DROP POLICY IF EXISTS platform_settings_tenant ON public.platform_settings;
    CREATE POLICY platform_settings_tenant ON public.platform_settings TO authenticated USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
  END IF;
  IF to_regclass('public.platform_health_checks') IS NOT NULL THEN
    DROP POLICY IF EXISTS platform_health_checks_tenant ON public.platform_health_checks;
    CREATE POLICY platform_health_checks_tenant ON public.platform_health_checks TO authenticated USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
  END IF;
  IF to_regclass('public.platform_security_events') IS NOT NULL THEN
    DROP POLICY IF EXISTS platform_security_events_tenant ON public.platform_security_events;
    CREATE POLICY platform_security_events_tenant ON public.platform_security_events TO authenticated USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
  END IF;
  IF to_regclass('public.tenant_limits') IS NOT NULL THEN
    DROP POLICY IF EXISTS tenant_limits_tenant ON public.tenant_limits;
    CREATE POLICY tenant_limits_tenant ON public.tenant_limits TO authenticated USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
  END IF;
  IF to_regclass('public.platform_usage_daily') IS NOT NULL THEN
    DROP POLICY IF EXISTS platform_usage_daily_tenant ON public.platform_usage_daily;
    CREATE POLICY platform_usage_daily_tenant ON public.platform_usage_daily TO authenticated USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
  END IF;
  IF to_regclass('public.platform_jobs') IS NOT NULL THEN
    DROP POLICY IF EXISTS platform_jobs_tenant ON public.platform_jobs;
    CREATE POLICY platform_jobs_tenant ON public.platform_jobs TO authenticated USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
  END IF;
  IF to_regclass('public.subscriptions') IS NOT NULL THEN
    DROP POLICY IF EXISTS subscriptions_tenant ON public.subscriptions;
    CREATE POLICY subscriptions_tenant ON public.subscriptions TO authenticated USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
  END IF;
  IF to_regclass('public.platform_events') IS NOT NULL THEN
    DROP POLICY IF EXISTS platform_events_tenant ON public.platform_events;
    CREATE POLICY platform_events_tenant ON public.platform_events TO authenticated USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
  END IF;
  IF to_regclass('public.onboarding_checklist') IS NOT NULL THEN
    DROP POLICY IF EXISTS onboarding_tenant ON public.onboarding_checklist;
    CREATE POLICY onboarding_tenant ON public.onboarding_checklist TO authenticated USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
  END IF;
  IF to_regclass('public.referrals') IS NOT NULL THEN
    DROP POLICY IF EXISTS referrals_tenant ON public.referrals;
    CREATE POLICY referrals_tenant ON public.referrals TO authenticated USING (referrer_clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)) OR converted_clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK (referrer_clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
  END IF;
  IF to_regclass('public.growth_campaign_events') IS NOT NULL THEN
    DROP POLICY IF EXISTS growth_events_tenant ON public.growth_campaign_events;
    CREATE POLICY growth_events_tenant ON public.growth_campaign_events TO authenticated USING (clinic_id IS NOT NULL AND clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
    IF to_regclass('public.growth_leads') IS NOT NULL AND NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='growth_events_clinic_lead_key' AND conrelid='public.growth_campaign_events'::regclass) THEN
      ALTER TABLE public.growth_campaign_events ADD CONSTRAINT growth_events_clinic_lead_key FOREIGN KEY (clinic_id,lead_id) REFERENCES public.growth_leads(clinic_id,id) ON DELETE SET NULL;
    END IF;
  END IF;
END $$;
