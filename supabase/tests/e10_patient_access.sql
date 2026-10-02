-- E10 database proof: tenant isolation, composite foreign keys and replay protection.
BEGIN;

INSERT INTO clinics(id,name,clerk_org_id) VALUES
 ('ci-e10-a','CI E10 A','ci_e10_org_a'),
 ('ci-e10-b','CI E10 B','ci_e10_org_b')
ON CONFLICT (id) DO NOTHING;

SET ROLE service_role;
SELECT set_config('app.clerk_org_id','ci_e10_org_a',false);

INSERT INTO patients(id,clinic_id,first_name,last_name)
VALUES ('ci-e10-patient-a','ci-e10-a','E10','Patient')
ON CONFLICT (id) DO NOTHING;

INSERT INTO provider_schedules(id,clinic_id,provider_id,specialty)
VALUES ('ci-e10-schedule-a','ci-e10-a','provider-a','primary-care')
ON CONFLICT (id) DO NOTHING;

INSERT INTO schedule_slots(id,clinic_id,schedule_id,provider_id,starts_at,ends_at,status)
VALUES ('ci-e10-slot-a','ci-e10-a','ci-e10-schedule-a','provider-a',
        '2031-01-01T10:00:00Z','2031-01-01T10:30:00Z','free')
ON CONFLICT (id) DO NOTHING;

SET CONSTRAINTS ALL IMMEDIATE;

RESET ROLE;
SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','ci_e10_org_a',false);

DO $
BEGIN
  IF NOT EXISTS (SELECT 1 FROM provider_schedules WHERE id='ci-e10-schedule-a') THEN
    RAISE EXCEPTION 'tenant A cannot read its own schedule';
  END IF;
END $;

SELECT set_config('app.clerk_org_id','ci_e10_org_b',false);

DO $$
BEGIN
  BEGIN
    INSERT INTO schedule_slots(id,clinic_id,schedule_id,provider_id,starts_at,ends_at,status)
    VALUES ('ci-e10-forged-slot','ci-e10-b','ci-e10-schedule-a','provider-b',
            '2031-01-01T11:00:00Z','2031-01-01T11:30:00Z','free');
    RAISE EXCEPTION 'cross-tenant schedule FK unexpectedly succeeded';
  EXCEPTION WHEN foreign_key_violation OR check_violation OR insufficient_privilege THEN NULL;
  END;
END $$;

DO $$
BEGIN
  BEGIN
    INSERT INTO patient_access_requests(id,clinic_id,patient_id,request_type,idempotency_key)
    VALUES ('ci-e10-forged-request','ci-e10-b','ci-e10-patient-a','appointment','ci-e10-forged-key');
    RAISE EXCEPTION 'cross-tenant patient FK unexpectedly succeeded';
  EXCEPTION WHEN foreign_key_violation OR check_violation OR insufficient_privilege THEN NULL;
  END;
END $$;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM provider_schedules WHERE id='ci-e10-schedule-a') THEN
    RAISE EXCEPTION 'cross-tenant schedule read';
  END IF;
  IF EXISTS (SELECT 1 FROM schedule_slots WHERE id='ci-e10-slot-a') THEN
    RAISE EXCEPTION 'cross-tenant slot read';
  END IF;
END $$;

RESET ROLE;
ROLLBACK;
