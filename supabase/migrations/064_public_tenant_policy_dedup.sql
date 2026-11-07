-- Migration 064: remove duplicate PUBLIC isolation policies only where
-- authenticated CRUD policies and a restrictive tenant boundary prove equivalence.
-- These legacy PUBLIC policies also applied to authenticated sessions, creating
-- four redundant permissive-policy paths per table.

DO $$
DECLARE
  policy_row record;
BEGIN
  FOR policy_row IN
    SELECT isolation_policy.schemaname, isolation_policy.tablename, isolation_policy.policyname
    FROM pg_policies isolation_policy
    WHERE isolation_policy.schemaname = 'public'
      AND isolation_policy.permissive = 'PERMISSIVE'
      AND isolation_policy.cmd = 'ALL'
      AND isolation_policy.roles = '{public}'
      AND isolation_policy.policyname LIKE '%isolation'
      AND EXISTS (
        SELECT 1 FROM pg_policies boundary
        WHERE boundary.schemaname = isolation_policy.schemaname
          AND boundary.tablename = isolation_policy.tablename
          AND boundary.policyname = 'e2_tenant_boundary'
          AND boundary.permissive = 'RESTRICTIVE'
          AND boundary.roles = '{authenticated}'
          AND boundary.cmd = 'ALL'
          AND boundary.qual IS NOT DISTINCT FROM isolation_policy.qual
          AND boundary.with_check IS NOT DISTINCT FROM isolation_policy.qual
      )
      AND EXISTS (
        SELECT 1 FROM pg_policies tenant_policy
        WHERE tenant_policy.schemaname = isolation_policy.schemaname
          AND tenant_policy.tablename = isolation_policy.tablename
          AND tenant_policy.policyname = 'hezqara_tenant_select'
          AND tenant_policy.permissive = 'PERMISSIVE'
          AND tenant_policy.roles = '{authenticated}'
          AND tenant_policy.cmd = 'SELECT'
          AND tenant_policy.qual IS NOT DISTINCT FROM isolation_policy.qual
      )
      AND EXISTS (
        SELECT 1 FROM pg_policies tenant_policy
        WHERE tenant_policy.schemaname = isolation_policy.schemaname
          AND tenant_policy.tablename = isolation_policy.tablename
          AND tenant_policy.policyname = 'hezqara_tenant_insert'
          AND tenant_policy.permissive = 'PERMISSIVE'
          AND tenant_policy.roles = '{authenticated}'
          AND tenant_policy.cmd = 'INSERT'
          AND tenant_policy.with_check IS NOT DISTINCT FROM isolation_policy.qual
      )
      AND EXISTS (
        SELECT 1 FROM pg_policies tenant_policy
        WHERE tenant_policy.schemaname = isolation_policy.schemaname
          AND tenant_policy.tablename = isolation_policy.tablename
          AND tenant_policy.policyname = 'hezqara_tenant_update'
          AND tenant_policy.permissive = 'PERMISSIVE'
          AND tenant_policy.roles = '{authenticated}'
          AND tenant_policy.cmd = 'UPDATE'
          AND tenant_policy.qual IS NOT DISTINCT FROM isolation_policy.qual
          AND tenant_policy.with_check IS NOT DISTINCT FROM isolation_policy.qual
      )
      AND EXISTS (
        SELECT 1 FROM pg_policies tenant_policy
        WHERE tenant_policy.schemaname = isolation_policy.schemaname
          AND tenant_policy.tablename = isolation_policy.tablename
          AND tenant_policy.policyname = 'hezqara_tenant_delete'
          AND tenant_policy.permissive = 'PERMISSIVE'
          AND tenant_policy.roles = '{authenticated}'
          AND tenant_policy.cmd = 'DELETE'
          AND tenant_policy.qual IS NOT DISTINCT FROM isolation_policy.qual
      )
      -- The public/anon role has no table privileges on these targets. Do not
      -- remove a PUBLIC policy if it is currently part of an anon-access path.
      AND NOT has_table_privilege(
        'anon',
        format('%I.%I', isolation_policy.schemaname, isolation_policy.tablename),
        'SELECT'
      )
      AND NOT has_table_privilege(
        'anon',
        format('%I.%I', isolation_policy.schemaname, isolation_policy.tablename),
        'INSERT'
      )
      AND NOT has_table_privilege(
        'anon',
        format('%I.%I', isolation_policy.schemaname, isolation_policy.tablename),
        'UPDATE'
      )
      AND NOT has_table_privilege(
        'anon',
        format('%I.%I', isolation_policy.schemaname, isolation_policy.tablename),
        'DELETE'
      )
  LOOP
    EXECUTE format(
      'DROP POLICY IF EXISTS %I ON %I.%I',
      policy_row.policyname, policy_row.schemaname, policy_row.tablename
    );
  END LOOP;
END $$;
