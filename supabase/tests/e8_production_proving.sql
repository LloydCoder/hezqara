-- E8 schema and tenant-boundary conformance.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['slo_definitions','slo_measurements','operational_incidents','operational_changes','recovery_drills','worker_heartbeats'] LOOP
    IF to_regclass('public.'||t) IS NULL THEN RAISE EXCEPTION 'missing E8 table %',t; END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_class c WHERE c.relname=t AND c.relrowsecurity) THEN RAISE EXCEPTION 'RLS missing on %',t; END IF;
  END LOOP;
END $$;

INSERT INTO clinics(id,name,clerk_org_id) VALUES
('e8-clinic-a','E8 Clinic A','e8-org-a'),
('e8-clinic-b','E8 Clinic B','e8-org-b')
ON CONFLICT (id) DO NOTHING;

INSERT INTO slo_definitions(clinic_id,name,target,metric) VALUES
('e8-clinic-a','api_availability',0.999,'availability');

INSERT INTO slo_measurements(clinic_id,window_start,window_end,good_events,total_events,achieved)
VALUES ('e8-clinic-a',now()-interval '1 day',now(),999,1000,0.999);

DO $$
BEGIN
  IF (SELECT achieved FROM slo_measurements WHERE clinic_id='e8-clinic-a' ORDER BY created_at DESC LIMIT 1) <> 0.999 THEN
    RAISE EXCEPTION 'SLO achievement calculation failed';
  END IF;
END $$;

DELETE FROM slo_measurements WHERE clinic_id='e8-clinic-a';
DELETE FROM slo_definitions WHERE clinic_id='e8-clinic-a';
DELETE FROM clinics WHERE id in ('e8-clinic-a','e8-clinic-b');
