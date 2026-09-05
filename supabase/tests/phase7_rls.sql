-- Phase 7 tenant isolation contract. Run as database owner against CI database.
INSERT INTO clinics(id,name,clerk_org_id) VALUES ('p7-a','Phase7 A','p7_org_a'),('p7-b','Phase7 B','p7_org_b') ON CONFLICT (id) DO NOTHING;
INSERT INTO integrations(clinic_id,name,category,provider_key,api_version) VALUES ('p7-a','A test EHR','ehr','test-ehr','test-v1'),('p7-b','B test EHR','ehr','test-ehr','test-v1') ON CONFLICT (clinic_id,provider_key) DO NOTHING;
INSERT INTO integration_credentials_metadata(clinic_id,integration_id,credential_ref,credential_type) SELECT clinic_id,id,'opaque-ref-'||clinic_id,'opaque' FROM integrations WHERE clinic_id IN ('p7-a','p7-b') ON CONFLICT DO NOTHING;
BEGIN;
SET LOCAL ROLE authenticated;
SET LOCAL app.clerk_org_id='p7_org_a';
DO $$ DECLARE n integer; BEGIN SELECT count(*) INTO n FROM integrations; IF n <> 1 THEN RAISE EXCEPTION 'tenant A integration isolation failed: %',n; END IF; SELECT count(*) INTO n FROM integration_credentials_metadata; IF n <> 1 THEN RAISE EXCEPTION 'tenant A credential metadata isolation failed: %',n; END IF; END $$;
SET LOCAL app.clerk_org_id='p7_org_b';
DO $$ DECLARE n integer; BEGIN SELECT count(*) INTO n FROM integrations; IF n <> 1 THEN RAISE EXCEPTION 'tenant B integration isolation failed: %',n; END IF; SELECT count(*) INTO n FROM integration_credentials_metadata; IF n <> 1 THEN RAISE EXCEPTION 'tenant B credential metadata isolation failed: %',n; END IF; END $$;
ROLLBACK;
