-- E2: canonical tenant isolation and relationship integrity.
-- Defense in depth: restrictive tenant policy, FORCE RLS, and tenant-bound
-- composite foreign keys. The authenticated role can only operate on rows
-- belonging to the Clerk organization resolved by app.clerk_org_id.
DO $$
DECLARE t text;
BEGIN
  FOR t IN
    SELECT c.table_name
    FROM information_schema.columns c
    JOIN information_schema.tables tb
      ON tb.table_schema=c.table_schema AND tb.table_name=c.table_name
    WHERE c.table_schema='public'
      AND tb.table_type='BASE TABLE'
      AND c.column_name='clinic_id'
  LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',t);
    EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY',t);
    EXECUTE format('DROP POLICY IF EXISTS e2_tenant_boundary ON public.%I',t);
    IF t='clinics' THEN
      EXECUTE 'CREATE POLICY e2_tenant_boundary ON public.clinics AS RESTRICTIVE FOR ALL TO authenticated USING (clerk_org_id=current_setting(''app.clerk_org_id'',true)) WITH CHECK (clerk_org_id=current_setting(''app.clerk_org_id'',true))';
    ELSE
      EXECUTE format(
        'CREATE POLICY e2_tenant_boundary ON public.%I AS RESTRICTIVE FOR ALL TO authenticated USING (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true))) WITH CHECK (clinic_id IN (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))',
        t
      );
    END IF;
    EXECUTE format('REVOKE ALL ON public.%I FROM anon',t);
  END LOOP;
END $$;

-- Every tenant-owned row gets a tenant-local identity key. Existing primary
-- keys remain globally unique; this second key makes cross-tenant references
-- impossible to represent when both objects carry clinic_id.
DO $$
DECLARE r record; constraint_name text;
BEGIN
  FOR r IN
    SELECT c.table_name
    FROM information_schema.columns c
    WHERE c.table_schema='public' AND c.column_name='clinic_id'
      AND EXISTS (
        SELECT 1 FROM information_schema.columns i
        WHERE i.table_schema='public' AND i.table_name=c.table_name AND i.column_name='id'
      )
  LOOP
    constraint_name := 'e2_' || substr(md5(r.table_name),1,16) || '_tenant_key';
    BEGIN
      EXECUTE format('ALTER TABLE public.%I ADD CONSTRAINT %I UNIQUE (clinic_id,id)',r.table_name,constraint_name);
    EXCEPTION WHEN duplicate_object THEN
      NULL;
    END;
  END LOOP;
END $$;

-- Add tenant-bound counterparts to existing single-column FKs between
-- tenant-owned tables. Existing FKs are intentionally retained as an
-- additional integrity layer.
DO $$
DECLARE r record; cname text;
BEGIN
  FOR r IN
    SELECT
      con.oid,
      child.relname child_table,
      parent.relname parent_table,
      child_col.attname child_column,
      parent_col.attname parent_column
    FROM pg_constraint con
    JOIN pg_class child ON child.oid=con.conrelid
    JOIN pg_class parent ON parent.oid=con.confrelid
    JOIN pg_namespace n1 ON n1.oid=child.relnamespace
    JOIN pg_namespace n2 ON n2.oid=parent.relnamespace
    JOIN pg_attribute child_col ON child_col.attrelid=child.oid AND child_col.attnum=con.conkey[1]
    JOIN pg_attribute parent_col ON parent_col.attrelid=parent.oid AND parent_col.attnum=con.confkey[1]
    WHERE con.contype='f'
      AND n1.nspname='public' AND n2.nspname='public'
      AND array_length(con.conkey,1)=1
      AND array_length(con.confkey,1)=1
      AND child_col.attname <> 'clinic_id'
      AND parent_col.attname = 'id'
      AND EXISTS (SELECT 1 FROM pg_attribute a WHERE a.attrelid=child.oid AND a.attname='clinic_id' AND a.attnum>0 AND NOT a.attisdropped)
      AND EXISTS (SELECT 1 FROM pg_attribute a WHERE a.attrelid=parent.oid AND a.attname='clinic_id' AND a.attnum>0 AND NOT a.attisdropped)
  LOOP
    cname := 'e2_fk_' || r.oid::text || '_tenant';
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname=cname AND conrelid=(r.child_table::regclass)) THEN
      EXECUTE format('ALTER TABLE public.%I ADD CONSTRAINT %I FOREIGN KEY (clinic_id,%I) REFERENCES public.%I(clinic_id,id)',r.child_table,cname,r.child_column,r.parent_table);
    END IF;
  END LOOP;
END $$;

-- Canonical tenant context is transaction-local and therefore safe with
-- pooled connections. No application request may choose a clinic_id directly
-- as its authority.
COMMENT ON SCHEMA public IS 'HEZQARA E2 tenant isolation: app.clerk_org_id is the authoritative request tenant; clinic_id is the canonical database tenant key.';
