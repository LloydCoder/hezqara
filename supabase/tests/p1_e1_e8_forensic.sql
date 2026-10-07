-- P1 forensic contract: every tenant-owned public table must remain RLS-protected.
-- This is intentionally structural and complements domain-specific isolation tests.
DO $$
DECLARE
  r record;
BEGIN
  FOR r IN
    SELECT DISTINCT c.table_name
    FROM information_schema.columns c
    JOIN information_schema.tables t
      ON t.table_schema=c.table_schema AND t.table_name=c.table_name
    WHERE c.table_schema='public'
      AND c.column_name='clinic_id'
      AND t.table_type='BASE TABLE'
      AND c.is_generated='NEVER'
  LOOP
    IF NOT EXISTS (
      SELECT 1
      FROM pg_class
      WHERE oid = format('public.%I',r.table_name)::regclass
        AND relrowsecurity
        AND relforcerowsecurity
    ) THEN
      RAISE EXCEPTION 'tenant-owned table is not FORCE RLS protected: %', r.table_name;
    END IF;

    IF has_table_privilege('anon', format('public.%I',r.table_name), 'SELECT')
       OR has_table_privilege('anon', format('public.%I',r.table_name), 'INSERT')
       OR has_table_privilege('anon', format('public.%I',r.table_name), 'UPDATE')
       OR has_table_privilege('anon', format('public.%I',r.table_name), 'DELETE') THEN
      RAISE EXCEPTION 'anon has direct privilege on tenant-owned table: %', r.table_name;
    END IF;
  END LOOP;
END $$;

-- The application role must not inherit privileged database roles.
DO $$
BEGIN
  IF pg_has_role('authenticated','service_role','member')
     OR pg_has_role('authenticated','postgres','member') THEN
    RAISE EXCEPTION 'authenticated role inherits a privileged role';
  END IF;
END $$;

-- Transaction-local tenant context is mandatory for the request-facing role.
BEGIN;
SET LOCAL ROLE authenticated;
SELECT set_config('app.clerk_org_id','p1-forensic-org',true);
DO $$
BEGIN
  IF current_setting('app.clerk_org_id',true) <> 'p1-forensic-org' THEN
    RAISE EXCEPTION 'tenant context was not established';
  END IF;
END $$;
ROLLBACK;
