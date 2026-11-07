-- Production schema advisor hardening regression checks.
DO $$
DECLARE
  fk_without_index integer;
  missing_fk_details text;
  multiple_policy_groups integer;
  unoptimized_policy_calls integer;
  duplicate_index_groups integer;
BEGIN
  IF EXISTS (
    SELECT 1
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relkind IN ('r','p')
      AND (NOT c.relrowsecurity OR NOT c.relforcerowsecurity)
  ) THEN
    RAISE EXCEPTION 'public application table is missing ENABLE/FORCE ROW LEVEL SECURITY';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
      AND p.proname IN (
        'update_updated_at','next_queue_number','reject_audit_mutation',
        'reject_workflow_history_mutation','prevent_appointment_overlap',
        'enforce_platform_usage_limit','healthy_worker_count',
        'recover_expired_execution_leases','workflow_step_runs_set_idempotency'
      )
      AND NOT (p.proconfig @> ARRAY['search_path=pg_catalog, public, pg_temp'])
  ) THEN
    RAISE EXCEPTION 'a protected public function is missing its explicit safe search_path';
  END IF;

  IF EXISTS (
    SELECT 1
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
      AND p.prosecdef
      AND (has_function_privilege('anon', p.oid, 'EXECUTE')
        OR has_function_privilege('authenticated', p.oid, 'EXECUTE'))
  ) THEN
    RAISE EXCEPTION 'an exposed SECURITY DEFINER function remains executable by anon/authenticated';
  END IF;

  IF has_function_privilege('anon', 'public.next_queue_number(text)', 'EXECUTE')
     OR has_function_privilege('authenticated', 'public.next_queue_number(text)', 'EXECUTE')
     OR NOT has_function_privilege('service_role', 'public.next_queue_number(text)', 'EXECUTE') THEN
    RAISE EXCEPTION 'next_queue_number has an invalid execution grant';
  END IF;

  IF has_function_privilege('anon', 'public.healthy_worker_count(interval)', 'EXECUTE')
     OR NOT has_function_privilege('authenticated', 'public.healthy_worker_count(interval)', 'EXECUTE')
     OR NOT has_function_privilege('service_role', 'public.healthy_worker_count(interval)', 'EXECUTE')
     OR (SELECT prosecdef FROM pg_proc WHERE oid='public.healthy_worker_count(interval)'::regprocedure) THEN
    RAISE EXCEPTION 'healthy_worker_count must be invoker-security and available only to authenticated/service_role';
  END IF;

  IF has_function_privilege('anon', 'public.recover_expired_execution_leases(timestamp with time zone)', 'EXECUTE')
     OR has_function_privilege('authenticated', 'public.recover_expired_execution_leases(timestamp with time zone)', 'EXECUTE')
     OR NOT has_function_privilege('service_role', 'public.recover_expired_execution_leases(timestamp with time zone)', 'EXECUTE') THEN
    RAISE EXCEPTION 'recover_expired_execution_leases has an invalid execution grant';
  END IF;

  WITH actions(action) AS (VALUES ('SELECT'),('INSERT'),('UPDATE'),('DELETE')),
  effective_policies AS (
    SELECT p.tablename, actions.action, p.policyname
    FROM pg_policies p
    CROSS JOIN actions
    WHERE p.schemaname = 'public'
      AND p.permissive = 'PERMISSIVE'
      AND (p.cmd = 'ALL' OR p.cmd = actions.action)
      AND (
        p.roles @> ARRAY['authenticated']::name[]
        OR p.roles @> ARRAY['public']::name[]
      )
  )
  SELECT count(*) INTO multiple_policy_groups
  FROM (
    SELECT tablename, action
    FROM effective_policies
    GROUP BY tablename, action
    HAVING count(*) > 1
  ) duplicates;

  IF multiple_policy_groups > 0 THEN
    RAISE EXCEPTION '% overlapping permissive RLS policy groups remain', multiple_policy_groups;
  END IF;

  SELECT count(*) INTO unoptimized_policy_calls
  FROM pg_policies p
  WHERE p.schemaname = 'public'
    AND (
      (p.qual IS NOT NULL AND (
        regexp_count(p.qual, 'current_setting\(') > regexp_count(p.qual, '\( SELECT current_setting\(')
        OR regexp_count(p.qual, 'auth\.[a-z_][a-z0-9_]*\(\)') > regexp_count(p.qual, '\( SELECT auth\.[a-z_][a-z0-9_]*\(\)')
      ))
      OR (p.with_check IS NOT NULL AND (
        regexp_count(p.with_check, 'current_setting\(') > regexp_count(p.with_check, '\( SELECT current_setting\(')
        OR regexp_count(p.with_check, 'auth\.[a-z_][a-z0-9_]*\(\)') > regexp_count(p.with_check, '\( SELECT auth\.[a-z_][a-z0-9_]*\(\)')
      ))
    );

  IF unoptimized_policy_calls > 0 THEN
    RAISE EXCEPTION '% RLS policies still call stable context functions per row', unoptimized_policy_calls;
  END IF;

  SELECT count(*) INTO duplicate_index_groups
  FROM (
    SELECT i.indrelid, i.indkey, i.indclass, i.indcollation, i.indoption,
           i.indpred, i.indexprs, i.indisunique, i.indnullsnotdistinct,
           i.indnkeyatts, i.indnatts, i.indimmediate, am.oid
    FROM pg_index i
    JOIN pg_class t ON t.oid = i.indrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    JOIN pg_class ix ON ix.oid = i.indexrelid
    JOIN pg_am am ON am.oid = ix.relam
    WHERE n.nspname = 'public'
      AND i.indisvalid
      AND i.indisready
    GROUP BY i.indrelid, i.indkey, i.indclass, i.indcollation, i.indoption,
             i.indpred, i.indexprs, i.indisunique, i.indnullsnotdistinct,
             i.indnkeyatts, i.indnatts, i.indimmediate, am.oid
    HAVING count(*) > 1
  ) duplicates;

  IF duplicate_index_groups > 0 THEN
    RAISE EXCEPTION '% duplicate index groups remain', duplicate_index_groups;
  END IF;

  SELECT count(*) INTO fk_without_index
  FROM (
    SELECT c.conrelid, c.conkey
    FROM pg_constraint c
    JOIN pg_namespace n ON n.oid = (SELECT relnamespace FROM pg_class WHERE oid = c.conrelid)
    WHERE c.contype = 'f'
      AND n.nspname = 'public'
    GROUP BY c.conrelid, c.conkey
  ) fk
  WHERE NOT EXISTS (
    SELECT 1
    FROM pg_index i
    JOIN pg_class ix ON ix.oid = i.indexrelid
    JOIN pg_am am ON am.oid = ix.relam
    WHERE i.indrelid = fk.conrelid
      AND i.indisvalid
      AND i.indisready
      AND i.indpred IS NULL
      AND i.indexprs IS NULL
      AND am.amname = 'btree'
      AND (i.indkey::smallint[])[0:cardinality(fk.conkey)-1] = fk.conkey
  );

  IF fk_without_index > 0 THEN
    SELECT string_agg(
      format('%s.%s constraint %s columns %s', missing.schema_name, missing.table_name, missing.constraint_name, missing.columns),
      '; '
    )
    INTO missing_fk_details
    FROM (
      SELECT n.nspname AS schema_name, t.relname AS table_name, c.conname AS constraint_name,
             array_agg(a.attname::text ORDER BY key_column.ordinality)::text AS columns
      FROM pg_constraint c
      JOIN pg_class t ON t.oid = c.conrelid
      JOIN pg_namespace n ON n.oid = t.relnamespace
      CROSS JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS key_column(attnum, ordinality)
      JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = key_column.attnum
      WHERE c.contype = 'f'
        AND n.nspname = 'public'
        AND NOT EXISTS (
          SELECT 1
          FROM pg_index i
          JOIN pg_class ix ON ix.oid = i.indexrelid
          JOIN pg_am am ON am.oid = ix.relam
          WHERE i.indrelid = c.conrelid
            AND i.indisvalid
            AND i.indisready
            AND i.indpred IS NULL
            AND i.indexprs IS NULL
            AND am.amname = 'btree'
            AND (i.indkey::smallint[])[0:cardinality(c.conkey)-1] = c.conkey
        )
      GROUP BY c.conrelid, c.conkey, n.nspname, t.relname, c.conname
    ) AS missing;
    RAISE EXCEPTION '% foreign-key column sets remain without a leading btree index: %', fk_without_index, missing_fk_details;
  END IF;
END $$;
