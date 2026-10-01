BEGIN;
INSERT INTO clinics(id,name,clerk_org_id) VALUES
  ('e7-tenant-a','E7 Tenant A','e7_org_a'),
  ('e7-tenant-b','E7 Tenant B','e7_org_b')
ON CONFLICT DO NOTHING;

SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','e7_org_a',false);

INSERT INTO clinic_activation(clinic_id,state,updated_by)
VALUES ('e7-tenant-a','ready','e7-user');
INSERT INTO activation_evidence(clinic_id,check_code,status,actor_id)
VALUES ('e7-tenant-a','tenant','passed','e7-user');
INSERT INTO roi_snapshots(clinic_id,period_start,period_end,workflow_runs)
VALUES ('e7-tenant-a',current_date,current_date,0);
INSERT INTO tenant_export_manifests(clinic_id,export_type,status,created_by)
VALUES ('e7-tenant-a','operational','ready','e7-user');

DO $$
BEGIN
  IF (SELECT count(*) FROM clinic_activation WHERE clinic_id='e7-tenant-b') <> 0 THEN
    RAISE EXCEPTION 'tenant B activation visible to tenant A';
  END IF;
  BEGIN
    INSERT INTO clinic_activation(clinic_id,state,updated_by)
    VALUES ('e7-tenant-b','ready','cross-tenant');
    RAISE EXCEPTION 'cross-tenant activation write unexpectedly succeeded';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
END $$;

RESET ROLE;
ROLLBACK;
