-- Run after migrations as a privileged database test harness.
BEGIN;
SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','tenant_a',false);
INSERT INTO ai_capabilities(id,clinic_id,name,description,domain,owner) VALUES ('test-cap','tenant_a','Test Capability','','test','test');
INSERT INTO ai_control_state(clinic_id) VALUES ('tenant_a') ON CONFLICT DO NOTHING;
SELECT set_config('app.clerk_org_id','tenant_b',false);
DO $$ BEGIN
 IF EXISTS (SELECT 1 FROM ai_capabilities WHERE clinic_id='tenant_a') THEN RAISE EXCEPTION 'ai_capabilities cross-tenant read'; END IF;
 IF EXISTS (SELECT 1 FROM ai_control_state WHERE clinic_id='tenant_a') THEN RAISE EXCEPTION 'ai_control_state cross-tenant read'; END IF;
END $$;
RESET ROLE;
ROLLBACK;
