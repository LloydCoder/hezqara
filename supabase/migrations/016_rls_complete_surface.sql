-- HEZQARA RLS completion.
-- Every public table that carries clinic_id must enforce the same tenant boundary
-- for Supabase Data API access. Application connections additionally set
-- app.clerk_org_id transaction-locally and must keep tenant predicates in repositories.

DO $$
DECLARE
  table_name text;
  has_clinic_id boolean;
BEGIN
  FOR table_name IN
    SELECT c.table_name
    FROM information_schema.tables c
    WHERE c.table_schema = 'public'
      AND c.table_type = 'BASE TABLE'
  LOOP
    SELECT EXISTS (
      SELECT 1
      FROM information_schema.columns col
      WHERE col.table_schema = 'public'
        AND col.table_name = table_name
        AND col.column_name = 'clinic_id'
    ) INTO has_clinic_id;

    IF has_clinic_id THEN
      EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);
      EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY', table_name);

      EXECUTE format('DROP POLICY IF EXISTS hezqara_tenant_select ON public.%I', table_name);
      EXECUTE format('DROP POLICY IF EXISTS hezqara_tenant_insert ON public.%I', table_name);
      EXECUTE format('DROP POLICY IF EXISTS hezqara_tenant_update ON public.%I', table_name);
      EXECUTE format('DROP POLICY IF EXISTS hezqara_tenant_delete ON public.%I', table_name);

      EXECUTE format(
        'CREATE POLICY hezqara_tenant_select ON public.%I FOR SELECT TO authenticated USING (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id = current_setting(''app.clerk_org_id'', true)))',
        table_name
      );
      EXECUTE format(
        'CREATE POLICY hezqara_tenant_insert ON public.%I FOR INSERT TO authenticated WITH CHECK (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id = current_setting(''app.clerk_org_id'', true)))',
        table_name
      );
      EXECUTE format(
        'CREATE POLICY hezqara_tenant_update ON public.%I FOR UPDATE TO authenticated USING (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id = current_setting(''app.clerk_org_id'', true))) WITH CHECK (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id = current_setting(''app.clerk_org_id'', true)))',
        table_name
      );
      EXECUTE format(
        'CREATE POLICY hezqara_tenant_delete ON public.%I FOR DELETE TO authenticated USING (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id = current_setting(''app.clerk_org_id'', true)))',
        table_name
      );

      EXECUTE format('REVOKE ALL ON public.%I FROM anon', table_name);
    END IF;
  END LOOP;
END $$;

-- Global configuration tables are not tenant records and must never be public.
DO $$
BEGIN
  IF to_regclass('public.whatsapp_templates') IS NOT NULL THEN
    ALTER TABLE public.whatsapp_templates ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.whatsapp_templates FORCE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS hezqara_whatsapp_templates_service ON public.whatsapp_templates;
    CREATE POLICY hezqara_whatsapp_templates_service
      ON public.whatsapp_templates FOR ALL TO service_role USING (true) WITH CHECK (true);
    REVOKE ALL ON public.whatsapp_templates FROM anon, authenticated;
  END IF;

  IF to_regclass('public.hmo_directory') IS NOT NULL THEN
    ALTER TABLE public.hmo_directory ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.hmo_directory FORCE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS hezqara_hmo_directory_service ON public.hmo_directory;
    CREATE POLICY hezqara_hmo_directory_service
      ON public.hmo_directory FOR ALL TO service_role USING (true) WITH CHECK (true);
    REVOKE ALL ON public.hmo_directory FROM anon;
  END IF;
END $$;

-- Outreach tables contain lead/contact data and are service-owned, not clinic-scoped.
DO $$
BEGIN
  IF to_regclass('public.waitlist') IS NOT NULL THEN
    ALTER TABLE public.waitlist ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.waitlist FORCE ROW LEVEL SECURITY;
    REVOKE ALL ON public.waitlist FROM anon, authenticated;
  END IF;
  IF to_regclass('public.outreach_log') IS NOT NULL THEN
    ALTER TABLE public.outreach_log ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.outreach_log FORCE ROW LEVEL SECURITY;
    REVOKE ALL ON public.outreach_log FROM anon, authenticated;
  END IF;
  IF to_regclass('public.demo_bookings') IS NOT NULL THEN
    ALTER TABLE public.demo_bookings ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.demo_bookings FORCE ROW LEVEL SECURITY;
    REVOKE ALL ON public.demo_bookings FROM anon, authenticated;
  END IF;
END $$;
