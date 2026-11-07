-- Migration 063: remove redundant permissive RLS policies and advisor-visible index overhead.
-- All policy removals are predicate-equivalent; all foreign keys are recreated before
-- their duplicate unique index is removed, preserving referential integrity.

-- 1) Remove redundant SELECT policies when an ALL/WRITE policy has the same role
-- and USING predicate. The ALL policy continues to authorize the exact same SELECTs.
DO $$
DECLARE
  policy_row record;
BEGIN
  FOR policy_row IN
    SELECT select_policy.schemaname, select_policy.tablename, select_policy.policyname
    FROM pg_policies select_policy
    JOIN pg_policies all_policy
      ON all_policy.schemaname = select_policy.schemaname
     AND all_policy.tablename = select_policy.tablename
     AND all_policy.roles = select_policy.roles
    WHERE select_policy.schemaname = 'public'
      AND select_policy.permissive = 'PERMISSIVE'
      AND all_policy.permissive = 'PERMISSIVE'
      AND select_policy.cmd = 'SELECT'
      AND all_policy.cmd = 'ALL'
      AND select_policy.policyname LIKE '%\_select' ESCAPE '\'
      AND all_policy.policyname LIKE '%\_write' ESCAPE '\'
      AND select_policy.qual IS NOT DISTINCT FROM all_policy.qual
  LOOP
    EXECUTE format(
      'DROP POLICY IF EXISTS %I ON %I.%I',
      policy_row.policyname, policy_row.schemaname, policy_row.tablename
    );
  END LOOP;

  -- Remove table-specific ALL isolation policies only when all four explicit
  -- hezqara_tenant_* CRUD policies exist with the identical tenant predicate.
  FOR policy_row IN
    SELECT isolation_policy.schemaname, isolation_policy.tablename, isolation_policy.policyname
    FROM pg_policies isolation_policy
    WHERE isolation_policy.schemaname = 'public'
      AND isolation_policy.permissive = 'PERMISSIVE'
      AND isolation_policy.cmd = 'ALL'
      AND isolation_policy.policyname LIKE '%isolation'
      AND EXISTS (
        SELECT 1 FROM pg_policies p
        WHERE p.schemaname = isolation_policy.schemaname
          AND p.tablename = isolation_policy.tablename
          AND p.roles = isolation_policy.roles
          AND p.policyname = 'hezqara_tenant_select'
          AND p.cmd = 'SELECT'
          AND p.qual IS NOT DISTINCT FROM isolation_policy.qual
      )
      AND EXISTS (
        SELECT 1 FROM pg_policies p
        WHERE p.schemaname = isolation_policy.schemaname
          AND p.tablename = isolation_policy.tablename
          AND p.roles = isolation_policy.roles
          AND p.policyname = 'hezqara_tenant_insert'
          AND p.cmd = 'INSERT'
          AND p.with_check IS NOT DISTINCT FROM isolation_policy.qual
      )
      AND EXISTS (
        SELECT 1 FROM pg_policies p
        WHERE p.schemaname = isolation_policy.schemaname
          AND p.tablename = isolation_policy.tablename
          AND p.roles = isolation_policy.roles
          AND p.policyname = 'hezqara_tenant_update'
          AND p.cmd = 'UPDATE'
          AND p.qual IS NOT DISTINCT FROM isolation_policy.qual
          AND p.with_check IS NOT DISTINCT FROM isolation_policy.qual
      )
      AND EXISTS (
        SELECT 1 FROM pg_policies p
        WHERE p.schemaname = isolation_policy.schemaname
          AND p.tablename = isolation_policy.tablename
          AND p.roles = isolation_policy.roles
          AND p.policyname = 'hezqara_tenant_delete'
          AND p.cmd = 'DELETE'
          AND p.qual IS NOT DISTINCT FROM isolation_policy.qual
      )
  LOOP
    EXECUTE format(
      'DROP POLICY IF EXISTS %I ON %I.%I',
      policy_row.policyname, policy_row.schemaname, policy_row.tablename
    );
  END LOOP;
END $$;

-- 2) Make stable RLS helper calls initplan-friendly. PostgreSQL evaluates the
-- scalar subselect once per statement rather than re-evaluating it per row.
DO $$
DECLARE
  policy_row record;
  rewritten_qual text;
  rewritten_check text;
BEGIN
  FOR policy_row IN
    SELECT schemaname, tablename, policyname, qual, with_check
    FROM pg_policies
    WHERE schemaname = 'public'
      AND (
        coalesce(qual, '') ~ 'current_setting\('
        OR coalesce(with_check, '') ~ 'current_setting\('
        OR coalesce(qual, '') ~ 'auth\.[a-z_][a-z0-9_]*\('
        OR coalesce(with_check, '') ~ 'auth\.[a-z_][a-z0-9_]*\('
      )
  LOOP
    rewritten_qual := policy_row.qual;
    rewritten_check := policy_row.with_check;

    IF rewritten_qual IS NOT NULL THEN
      rewritten_qual := regexp_replace(
        rewritten_qual,
        $re$current_setting\(([^()]*)\)$re$,
        $rep$( SELECT current_setting(\1) )$rep$,
        'g'
      );
      rewritten_qual := regexp_replace(
        rewritten_qual,
        $re$auth\.([a-z_][a-z0-9_]*)\(\)$re$,
        $rep$( SELECT auth.\1() )$rep$,
        'g'
      );
    END IF;

    IF rewritten_check IS NOT NULL THEN
      rewritten_check := regexp_replace(
        rewritten_check,
        $re$current_setting\(([^()]*)\)$re$,
        $rep$( SELECT current_setting(\1) )$rep$,
        'g'
      );
      rewritten_check := regexp_replace(
        rewritten_check,
        $re$auth\.([a-z_][a-z0-9_]*)\(\)$re$,
        $rep$( SELECT auth.\1() )$rep$,
        'g'
      );
    END IF;

    IF rewritten_qual IS DISTINCT FROM policy_row.qual THEN
      EXECUTE format(
        'ALTER POLICY %I ON %I.%I USING (%s)',
        policy_row.policyname, policy_row.schemaname, policy_row.tablename, rewritten_qual
      );
    END IF;

    IF rewritten_check IS DISTINCT FROM policy_row.with_check THEN
      EXECUTE format(
        'ALTER POLICY %I ON %I.%I WITH CHECK (%s)',
        policy_row.policyname, policy_row.schemaname, policy_row.tablename, rewritten_check
      );
    END IF;
  END LOOP;
END $$;

-- 3) The E2 tenant-key UNIQUE constraints duplicate an existing PRIMARY KEY or
-- UNIQUE constraint on the same columns. Rebind any FKs to the surviving
-- equivalent key, then remove only the redundant e2_*_tenant_key constraint.
CREATE TEMP TABLE _hezqara_fk_rebind_063 (
  source_index_oid oid NOT NULL,
  referencing_schema text NOT NULL,
  referencing_table text NOT NULL,
  constraint_name text NOT NULL,
  constraint_definition text NOT NULL
) ON COMMIT PRESERVE ROWS;

DO $$
DECLARE
  duplicate_constraint record;
  foreign_key record;
BEGIN
  FOR duplicate_constraint IN
    SELECT e2_constraint.oid AS constraint_oid,
           e2_constraint.conrelid,
           e2_constraint.conname AS constraint_name,
           e2_constraint.conindid AS index_oid,
           table_namespace.nspname AS schema_name,
           table_class.relname AS table_name,
           target_index.indkey,
           target_index.indclass,
           target_index.indcollation,
           target_index.indoption,
           target_index.indpred,
           target_index.indexprs,
           target_index.indisunique,
           target_index.indnullsnotdistinct,
           target_index.indnkeyatts,
           target_index.indnatts,
           target_index.indimmediate,
           target_am.oid AS access_method_oid
    FROM pg_constraint e2_constraint
    JOIN pg_class table_class ON table_class.oid = e2_constraint.conrelid
    JOIN pg_namespace table_namespace ON table_namespace.oid = table_class.relnamespace
    JOIN pg_index target_index ON target_index.indexrelid = e2_constraint.conindid
    JOIN pg_class target_index_class ON target_index_class.oid = target_index.indexrelid
    JOIN pg_am target_am ON target_am.oid = target_index_class.relam
    WHERE table_namespace.nspname = 'public'
      AND e2_constraint.contype = 'u'
      AND e2_constraint.conname LIKE 'e2\_%\_tenant_key' ESCAPE '\'
      AND EXISTS (
        SELECT 1
        FROM pg_index other_index
        JOIN pg_class other_index_class ON other_index_class.oid = other_index.indexrelid
        JOIN pg_am other_am ON other_am.oid = other_index_class.relam
        JOIN pg_constraint other_constraint ON other_constraint.conindid = other_index.indexrelid
        WHERE other_index.indrelid = target_index.indrelid
          AND other_index.indexrelid <> target_index.indexrelid
          AND other_constraint.contype IN ('p','u')
          AND other_index.indkey = target_index.indkey
          AND other_index.indclass = target_index.indclass
          AND other_index.indcollation = target_index.indcollation
          AND other_index.indoption = target_index.indoption
          AND other_index.indpred IS NOT DISTINCT FROM target_index.indpred
          AND other_index.indexprs IS NOT DISTINCT FROM target_index.indexprs
          AND other_index.indisunique = target_index.indisunique
          AND other_index.indnullsnotdistinct = target_index.indnullsnotdistinct
          AND other_index.indnkeyatts = target_index.indnkeyatts
          AND other_index.indnatts = target_index.indnatts
          AND other_index.indimmediate = target_index.indimmediate
          AND other_am.oid = target_am.oid
      )
    ORDER BY table_class.relname, e2_constraint.conname
  LOOP
    INSERT INTO pg_temp._hezqara_fk_rebind_063 (
      source_index_oid, referencing_schema, referencing_table, constraint_name, constraint_definition
    )
    SELECT duplicate_constraint.index_oid,
           referencing_namespace.nspname,
           referencing_table.relname,
           fk.conname,
           pg_get_constraintdef(fk.oid)
    FROM pg_constraint fk
    JOIN pg_class referencing_table ON referencing_table.oid = fk.conrelid
    JOIN pg_namespace referencing_namespace ON referencing_namespace.oid = referencing_table.relnamespace
    WHERE fk.contype = 'f'
      AND fk.conindid = duplicate_constraint.index_oid;

    FOR foreign_key IN
      SELECT *
      FROM pg_temp._hezqara_fk_rebind_063
      WHERE source_index_oid = duplicate_constraint.index_oid
    LOOP
      EXECUTE format(
        'ALTER TABLE %I.%I DROP CONSTRAINT %I',
        foreign_key.referencing_schema, foreign_key.referencing_table, foreign_key.constraint_name
      );
    END LOOP;

    EXECUTE format(
      'ALTER TABLE %I.%I DROP CONSTRAINT %I',
      duplicate_constraint.schema_name, duplicate_constraint.table_name, duplicate_constraint.constraint_name
    );

    FOR foreign_key IN
      SELECT *
      FROM pg_temp._hezqara_fk_rebind_063
      WHERE source_index_oid = duplicate_constraint.index_oid
    LOOP
      EXECUTE format(
        'ALTER TABLE %I.%I ADD CONSTRAINT %I %s',
        foreign_key.referencing_schema, foreign_key.referencing_table,
        foreign_key.constraint_name, foreign_key.constraint_definition
      );
    END LOOP;

    DELETE FROM pg_temp._hezqara_fk_rebind_063
    WHERE source_index_oid = duplicate_constraint.index_oid;
  END LOOP;
END $$;

DROP TABLE pg_temp._hezqara_fk_rebind_063;
