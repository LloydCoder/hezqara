-- Integrated tenant-isolation proof for Phase 9-13 additions.
BEGIN;
INSERT INTO clinics(id,name,clerk_org_id) VALUES
 ('ci-tenant-a','CI Tenant A','ci_org_a'),
 ('ci-tenant-b','CI Tenant B','ci_org_b')
 ON CONFLICT (id) DO NOTHING;

SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','ci_org_a',false);
INSERT INTO ai_capabilities(id,clinic_id,name,description,domain,owner,risk_tier)
VALUES ('ci-cap','ci-tenant-a','CI Capability','','test','ci',1)
ON CONFLICT DO NOTHING;
INSERT INTO ai_evaluation_suites(clinic_id,capability_id,version,name)
VALUES ('ci-tenant-a','ci-cap','1.0','CI Suite') ON CONFLICT DO NOTHING;
INSERT INTO platform_settings(clinic_id) VALUES ('ci-tenant-a') ON CONFLICT DO NOTHING;
INSERT INTO tenant_limits(clinic_id) VALUES ('ci-tenant-a') ON CONFLICT DO NOTHING;
INSERT INTO subscriptions(clinic_id,plan_code,status) VALUES ('ci-tenant-a','starter','active') ON CONFLICT DO NOTHING;
INSERT INTO onboarding_checklist(clinic_id,step,status) VALUES ('ci-tenant-a','clinic_profile','completed') ON CONFLICT DO NOTHING;
INSERT INTO growth_leads(clinic_id,email,clinic_name) VALUES ('ci-tenant-a','ci-a@example.test','CI A') ON CONFLICT DO NOTHING;
INSERT INTO growth_campaign_events(clinic_id,lead_id,event_type)
SELECT 'ci-tenant-a',id,'created' FROM growth_leads WHERE clinic_id='ci-tenant-a' AND email='ci-a@example.test';

SELECT set_config('app.clerk_org_id','ci_org_b',false);
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM ai_capabilities WHERE clinic_id='ci-tenant-a') THEN RAISE EXCEPTION 'cross-tenant capability read'; END IF;
  IF EXISTS (SELECT 1 FROM platform_settings WHERE clinic_id='ci-tenant-a') THEN RAISE EXCEPTION 'cross-tenant settings read'; END IF;
  IF EXISTS (SELECT 1 FROM tenant_limits WHERE clinic_id='ci-tenant-a') THEN RAISE EXCEPTION 'cross-tenant limits read'; END IF;
  IF EXISTS (SELECT 1 FROM subscriptions WHERE clinic_id='ci-tenant-a') THEN RAISE EXCEPTION 'cross-tenant subscription read'; END IF;
  IF EXISTS (SELECT 1 FROM onboarding_checklist WHERE clinic_id='ci-tenant-a') THEN RAISE EXCEPTION 'cross-tenant onboarding read'; END IF;
  IF EXISTS (SELECT 1 FROM growth_leads WHERE clinic_id='ci-tenant-a') THEN RAISE EXCEPTION 'cross-tenant growth lead read'; END IF;
  IF EXISTS (SELECT 1 FROM growth_campaign_events WHERE clinic_id='ci-tenant-a') THEN RAISE EXCEPTION 'cross-tenant growth event read'; END IF;
END $$;

DO $$ BEGIN
  BEGIN
    INSERT INTO platform_settings(clinic_id) VALUES ('ci-tenant-a');
    RAISE EXCEPTION 'cross-tenant forged insert unexpectedly succeeded';
  EXCEPTION WHEN others THEN
    IF SQLERRM LIKE 'cross-tenant forged insert unexpectedly succeeded' THEN RAISE; END IF;
  END;
END $$;

DO $$ BEGIN
  BEGIN
    INSERT INTO growth_leads(clinic_id,email,clinic_name) VALUES ('ci-tenant-a','ci-forged@example.test','forged');
    RAISE EXCEPTION 'cross-tenant growth lead insert unexpectedly succeeded';
  EXCEPTION WHEN others THEN
    IF SQLERRM LIKE 'cross-tenant growth lead insert unexpectedly succeeded' THEN RAISE; END IF;
  END;
END $$;

RESET ROLE;
ROLLBACK;
