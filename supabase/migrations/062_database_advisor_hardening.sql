-- Migration 062: close Supabase database-advisor findings without weakening tenant controls.
-- Trigger functions are not public RPCs. Operational functions are restricted to service_role.
-- All function search paths are explicit and place pg_catalog before application schemas.

ALTER FUNCTION public.update_updated_at()
  SET search_path TO pg_catalog, public, pg_temp;
ALTER FUNCTION public.next_queue_number(text)
  SET search_path TO pg_catalog, public, pg_temp;
ALTER FUNCTION public.reject_audit_mutation()
  SET search_path TO pg_catalog, public, pg_temp;
ALTER FUNCTION public.reject_workflow_history_mutation()
  SET search_path TO pg_catalog, public, pg_temp;
ALTER FUNCTION public.prevent_appointment_overlap()
  SET search_path TO pg_catalog, public, pg_temp;
ALTER FUNCTION public.enforce_platform_usage_limit()
  SET search_path TO pg_catalog, public, pg_temp;
ALTER FUNCTION public.healthy_worker_count(interval)
  SET search_path TO pg_catalog, public, pg_temp;
ALTER FUNCTION public.recover_expired_execution_leases(timestamp with time zone)
  SET search_path TO pg_catalog, public, pg_temp;
ALTER FUNCTION public.workflow_step_runs_set_idempotency()
  SET search_path TO pg_catalog, public, pg_temp;

-- New functions created by the migration owner must not inherit PUBLIC execution.
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC, anon, authenticated;

-- Trigger-only functions must not be callable as PostgREST RPCs.
REVOKE ALL ON FUNCTION public.update_updated_at() FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.reject_audit_mutation() FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.reject_workflow_history_mutation() FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.prevent_appointment_overlap() FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.enforce_platform_usage_limit() FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON FUNCTION public.workflow_step_runs_set_idempotency() FROM PUBLIC, anon, authenticated, service_role;

-- These operational functions are callable by trusted backend/service-role processes only.
REVOKE ALL ON FUNCTION public.next_queue_number(text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.next_queue_number(text) TO service_role;
REVOKE ALL ON FUNCTION public.healthy_worker_count(interval) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.healthy_worker_count(interval) TO service_role;
REVOKE ALL ON FUNCTION public.recover_expired_execution_leases(timestamp with time zone) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.recover_expired_execution_leases(timestamp with time zone) TO service_role;

-- Keep the single canonical tenant policy on each affected table. The removed
-- policies have the same predicate and only caused permissive-policy OR duplication.
DROP POLICY IF EXISTS e11_tenant_write ON public.authorizations;
DROP POLICY IF EXISTS phase6_tenant_write ON public.authorizations;
DROP POLICY IF EXISTS e11_tenant_select ON public.authorizations;
DROP POLICY IF EXISTS phase6_tenant_select ON public.authorizations;
DROP POLICY IF EXISTS e11_tenant_write ON public.eligibility_requests;
DROP POLICY IF EXISTS phase6_tenant_write ON public.eligibility_requests;
DROP POLICY IF EXISTS e11_tenant_select ON public.eligibility_requests;
DROP POLICY IF EXISTS phase6_tenant_select ON public.eligibility_requests;
DROP POLICY IF EXISTS e11_tenant_write ON public.patient_coverages;
DROP POLICY IF EXISTS phase6_tenant_write ON public.patient_coverages;
DROP POLICY IF EXISTS e11_tenant_select ON public.patient_coverages;
DROP POLICY IF EXISTS phase6_tenant_select ON public.patient_coverages;
DROP POLICY IF EXISTS e11_tenant_write ON public.records_v2;
DROP POLICY IF EXISTS phase6_tenant_write ON public.records_v2;
DROP POLICY IF EXISTS e11_tenant_select ON public.records_v2;
DROP POLICY IF EXISTS phase6_tenant_select ON public.records_v2;

-- Add one btree index for each distinct FK column set that lacks a suitable
-- leading-column index. This improves joins and parent-row update/delete checks.
DO $$
DECLARE
  fk record;
  column_sql text;
  index_name text;
BEGIN
  FOR fk IN
    SELECT c.conrelid, c.conkey, n.nspname AS schema_name, t.relname AS table_name,
           array_agg(a.attname::text ORDER BY key_column.ordinality) AS column_names
    FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    CROSS JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS key_column(attnum, ordinality)
    JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = key_column.attnum
    WHERE c.contype = 'f'
      AND n.nspname = 'public'
    GROUP BY c.conrelid, c.conkey, n.nspname, t.relname
  LOOP
    IF NOT EXISTS (
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
    ) THEN
      SELECT string_agg(format('%I', col_name), ', ')
        INTO column_sql
      FROM unnest(fk.column_names) AS cols(col_name);

      index_name := 'idx_fk_' || substr(md5(fk.table_name || ':' || array_to_string(fk.column_names, ':')), 1, 20);

      IF to_regclass(format('%I.%I', fk.schema_name, index_name)) IS NULL THEN
        EXECUTE format(
          'CREATE INDEX %I ON %I.%I (%s)',
          index_name, fk.schema_name, fk.table_name, column_sql
        );
      END IF;
    END IF;
  END LOOP;
END $$;

-- Remove exact duplicate indexes only when the redundant index is not owned by
-- a PRIMARY KEY / UNIQUE / EXCLUSION constraint and is not the replica identity
-- or clustered index. Constraint-backed indexes are deliberately preserved.
DO $$
DECLARE
  duplicate_group record;
  keep_index oid;
  candidate record;
BEGIN
  FOR duplicate_group IN
    SELECT i.indrelid, i.indkey, i.indclass, i.indcollation, i.indoption,
           i.indpred, i.indexprs, i.indisunique, i.indnullsnotdistinct,
           i.indnkeyatts, i.indnatts, i.indisprimary, i.indisexclusion,
           i.indimmediate, am.oid AS access_method_oid
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
             i.indnkeyatts, i.indnatts, i.indisprimary, i.indisexclusion,
             i.indimmediate, am.oid
    HAVING count(*) > 1
  LOOP
    keep_index := NULL;

    SELECT i.indexrelid
      INTO keep_index
    FROM pg_index i
    JOIN pg_class ix ON ix.oid = i.indexrelid
    JOIN pg_am am ON am.oid = ix.relam
    WHERE i.indrelid = duplicate_group.indrelid
      AND i.indkey = duplicate_group.indkey
      AND i.indclass = duplicate_group.indclass
      AND i.indcollation = duplicate_group.indcollation
      AND i.indoption = duplicate_group.indoption
      AND i.indpred IS NOT DISTINCT FROM duplicate_group.indpred
      AND i.indexprs IS NOT DISTINCT FROM duplicate_group.indexprs
      AND i.indisunique = duplicate_group.indisunique
      AND i.indnullsnotdistinct = duplicate_group.indnullsnotdistinct
      AND i.indnkeyatts = duplicate_group.indnkeyatts
      AND i.indnatts = duplicate_group.indnatts
      AND i.indisprimary = duplicate_group.indisprimary
      AND i.indisexclusion = duplicate_group.indisexclusion
      AND i.indimmediate = duplicate_group.indimmediate
      AND am.oid = duplicate_group.access_method_oid
      AND EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conindid = i.indexrelid)
    ORDER BY ix.relname
    LIMIT 1;

    IF keep_index IS NULL THEN
      SELECT i.indexrelid
        INTO keep_index
      FROM pg_index i
      JOIN pg_class ix ON ix.oid = i.indexrelid
      JOIN pg_am am ON am.oid = ix.relam
      WHERE i.indrelid = duplicate_group.indrelid
        AND i.indkey = duplicate_group.indkey
        AND i.indclass = duplicate_group.indclass
        AND i.indcollation = duplicate_group.indcollation
        AND i.indoption = duplicate_group.indoption
        AND i.indpred IS NOT DISTINCT FROM duplicate_group.indpred
        AND i.indexprs IS NOT DISTINCT FROM duplicate_group.indexprs
        AND i.indisunique = duplicate_group.indisunique
        AND i.indnullsnotdistinct = duplicate_group.indnullsnotdistinct
        AND i.indnkeyatts = duplicate_group.indnkeyatts
        AND i.indnatts = duplicate_group.indnatts
        AND i.indisprimary = duplicate_group.indisprimary
        AND i.indisexclusion = duplicate_group.indisexclusion
        AND i.indimmediate = duplicate_group.indimmediate
        AND am.oid = duplicate_group.access_method_oid
      ORDER BY ix.relname
      LIMIT 1;
    END IF;

    FOR candidate IN
      SELECT i.indexrelid, n.nspname AS schema_name, ix.relname AS index_name
      FROM pg_index i
      JOIN pg_class ix ON ix.oid = i.indexrelid
      JOIN pg_namespace n ON n.oid = ix.relnamespace
      JOIN pg_am am ON am.oid = ix.relam
      WHERE i.indrelid = duplicate_group.indrelid
        AND i.indkey = duplicate_group.indkey
        AND i.indclass = duplicate_group.indclass
        AND i.indcollation = duplicate_group.indcollation
        AND i.indoption = duplicate_group.indoption
        AND i.indpred IS NOT DISTINCT FROM duplicate_group.indpred
        AND i.indexprs IS NOT DISTINCT FROM duplicate_group.indexprs
        AND i.indisunique = duplicate_group.indisunique
        AND i.indnullsnotdistinct = duplicate_group.indnullsnotdistinct
        AND i.indnkeyatts = duplicate_group.indnkeyatts
        AND i.indnatts = duplicate_group.indnatts
        AND i.indisprimary = duplicate_group.indisprimary
        AND i.indisexclusion = duplicate_group.indisexclusion
        AND i.indimmediate = duplicate_group.indimmediate
        AND am.oid = duplicate_group.access_method_oid
        AND i.indexrelid <> keep_index
        AND NOT i.indisreplident
        AND NOT i.indisclustered
        AND NOT EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conindid = i.indexrelid)
      ORDER BY ix.relname
    LOOP
      EXECUTE format('DROP INDEX IF EXISTS %I.%I', candidate.schema_name, candidate.index_name);
    END LOOP;
  END LOOP;
END $$;
