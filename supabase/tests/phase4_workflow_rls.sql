-- Phase 4 database security proof: workflow objects remain tenant-isolated at the PostgreSQL boundary.
INSERT INTO clinics(id,name,clerk_org_id) VALUES ('phase4-a','Phase4 A','phase4_org_a'),('phase4-b','Phase4 B','phase4_org_b') ON CONFLICT (id) DO NOTHING;
INSERT INTO workflows(id,clinic_id,key,name,created_by) VALUES ('phase4-wf-a','phase4-a','a-only','A workflow','test'),('phase4-wf-b','phase4-b','b-only','B workflow','test') ON CONFLICT (id) DO NOTHING;
BEGIN;
SET LOCAL ROLE authenticated;
SELECT set_config('app.clerk_org_id','phase4_org_a',true);
DO $$ BEGIN
  IF (SELECT count(*) FROM workflows WHERE key='a-only') <> 1 THEN RAISE EXCEPTION 'tenant A cannot read its own workflow'; END IF;
  IF (SELECT count(*) FROM workflows WHERE key='b-only') <> 0 THEN RAISE EXCEPTION 'tenant A can read tenant B workflow'; END IF;
  BEGIN
    INSERT INTO workflows(id,clinic_id,key,name,created_by) VALUES ('phase4-forbidden','phase4-b','forbidden','Forbidden','test');
    RAISE EXCEPTION 'tenant A inserted tenant B workflow';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
END $$;
ROLLBACK;
