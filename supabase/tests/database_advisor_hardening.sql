-- Production schema advisor hardening regression checks.
DO $$
DECLARE
  fk_without_index integer;
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

  IF EXISTS (
    SELECT 1
    FROM pg_policies
    WHERE schemaname = 'public'
      AND permissive = 'PERMISSIVE'
    GROUP BY tablename, roles, cmd
    HAVING count(*) > 1
  ) THEN
    RAISE EXCEPTION 'duplicate permissive RLS policy groups remain';
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
    RAISE EXCEPTION '% foreign-key column sets remain without a leading btree index', fk_without_index;
  END IF;
END $$;
