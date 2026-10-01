-- Post-E8 forensic hardening: operational evidence is platform-owned and
-- worker liveness must not be mutable by tenant users.

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['operational_incidents','operational_changes','recovery_drills'] LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',t);
    EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY',t);
    EXECUTE format('REVOKE ALL ON public.%I FROM anon',t);
    EXECUTE format('REVOKE INSERT,UPDATE,DELETE ON public.%I FROM authenticated',t);
    EXECUTE format('GRANT SELECT ON public.%I TO authenticated',t);
    EXECUTE format('DROP POLICY IF EXISTS e8_tenant_boundary ON public.%I',t);
    EXECUTE format('DROP POLICY IF EXISTS e8_tenant_access ON public.%I',t);
    EXECUTE format(
      'CREATE POLICY e8_tenant_boundary ON public.%I AS RESTRICTIVE FOR SELECT TO authenticated
       USING (clinic_id IS NOT NULL AND clinic_id IN
         (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))',
      t
    );
    EXECUTE format(
      'CREATE POLICY e8_tenant_access ON public.%I AS PERMISSIVE FOR SELECT TO authenticated
       USING (clinic_id IS NOT NULL AND clinic_id IN
         (SELECT id FROM public.clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))',
      t
    );
  END LOOP;
END $$;

ALTER TABLE public.worker_heartbeats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.worker_heartbeats FORCE ROW LEVEL SECURITY;
REVOKE ALL ON public.worker_heartbeats FROM anon;
REVOKE ALL ON public.worker_heartbeats FROM authenticated;

DROP POLICY IF EXISTS e8_heartbeat_boundary ON public.worker_heartbeats;
DROP POLICY IF EXISTS e8_heartbeat_access ON public.worker_heartbeats;
CREATE POLICY e8_heartbeat_boundary ON public.worker_heartbeats AS RESTRICTIVE FOR ALL TO authenticated USING (false) WITH CHECK (false);
CREATE POLICY e8_heartbeat_access ON public.worker_heartbeats AS PERMISSIVE FOR ALL TO authenticated USING (false) WITH CHECK (false);

CREATE OR REPLACE FUNCTION public.healthy_worker_count(p_max_age interval DEFAULT interval '2 minutes')
RETURNS bigint
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = public, pg_temp
AS $$
  SELECT count(*)::bigint
  FROM public.worker_heartbeats
  WHERE last_seen_at >= now() - p_max_age;
$$;

REVOKE ALL ON FUNCTION public.healthy_worker_count(interval) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.healthy_worker_count(interval) TO authenticated;

COMMENT ON FUNCTION public.healthy_worker_count(interval)
IS 'Read-only platform worker liveness summary. Table writes remain system-owned.';
