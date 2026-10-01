-- E2 adversarial tenant-isolation verification.
-- Run after all migrations as a privileged database test harness.
BEGIN;
INSERT INTO clinics(id,name,clerk_org_id) VALUES
 ('e2_tenant_a','E2 Tenant A','e2_org_a'),
 ('e2_tenant_b','E2 Tenant B','e2_org_b')
ON CONFLICT (id) DO NOTHING;

SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','e2_org_a',false);
INSERT INTO patients(id,clinic_id,first_name,last_name) VALUES ('e2_patient_a','e2_tenant_a','A','Patient');
SELECT set_config('app.clerk_org_id','e2_org_b',false);
INSERT INTO patients(id,clinic_id,first_name,last_name) VALUES ('e2_patient_b','e2_tenant_b','B','Patient');

SELECT set_config('app.clerk_org_id','e2_org_a',false);
DO $$ BEGIN
  IF (SELECT count(*) FROM patients WHERE id IN ('e2_patient_a','e2_patient_b')) <> 1 THEN
    RAISE EXCEPTION 'E2 cross-tenant read isolation failed';
  END IF;
END $$;

DO $$ BEGIN
  BEGIN
    INSERT INTO patients(id,clinic_id,first_name,last_name) VALUES ('e2_forged','e2_tenant_b','Forged','Patient');
    RAISE EXCEPTION 'E2 forged clinic insert was accepted';
  EXCEPTION WHEN insufficient_privilege OR check_violation THEN NULL;
  END;
END $$;

DO $$ BEGIN
  BEGIN
    UPDATE patients SET clinic_id='e2_tenant_b' WHERE id='e2_patient_a';
    RAISE EXCEPTION 'E2 tenant reassignment was accepted';
  EXCEPTION WHEN insufficient_privilege OR check_violation THEN NULL;
  END;
END $$;

DO $$ BEGIN
  BEGIN
    INSERT INTO appointments(id,clinic_id,patient_id,appointment_datetime)
      VALUES ('e2_cross_tenant_appointment','e2_tenant_a','e2_patient_b',now());
    RAISE EXCEPTION 'E2 cross-tenant relationship was accepted';
  EXCEPTION WHEN foreign_key_violation OR check_violation OR insufficient_privilege THEN NULL;
  END;
END $$;

RESET ROLE;

DO $$ DECLARE r record; BEGIN
  FOR r IN
    SELECT c.table_name
    FROM information_schema.columns c
    JOIN information_schema.tables t ON t.table_schema=c.table_schema AND t.table_name=c.table_name
    WHERE c.table_schema='public' AND t.table_type='BASE TABLE' AND c.column_name='clinic_id'
  LOOP
    IF NOT EXISTS (SELECT 1 FROM pg_class pc JOIN pg_namespace pn ON pn.oid=pc.relnamespace WHERE pn.nspname='public' AND pc.relname=r.table_name AND pc.relrowsecurity AND pc.relforcerowsecurity) THEN
      RAISE EXCEPTION 'E2 RLS not forced on %',r.table_name;
    END IF;
  END LOOP;
END $$;
ROLLBACK;
