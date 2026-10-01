-- E4 interoperability metadata and standards boundary verification.
BEGIN;
INSERT INTO clinics(id,name,clerk_org_id) VALUES ('e4-tenant','E4 Tenant','e4_org') ON CONFLICT DO NOTHING;
SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','e4_org',false);
INSERT INTO integrations(id,clinic_id,name,category,provider_key,api_version,environment,base_url,smart_version,auth_method)
VALUES ('00000000-0000-0000-0000-000000000037','e4-tenant','E4 FHIR','fhir','test-fhir','R4','test','https://ehr.example.com','2.2.0','smart_public_pkce')
ON CONFLICT (clinic_id,provider_key) DO NOTHING;
INSERT INTO integration_protocol_capabilities(clinic_id,integration_id,protocol,version,configuration)
VALUES ('e4-tenant','00000000-0000-0000-0000-000000000037','FHIR','4.0.1','{"resource_profiles":["Patient","Coverage","Claim","ClaimResponse"]}')
ON CONFLICT DO NOTHING;
INSERT INTO integration_oauth_sessions(clinic_id,integration_id,state,code_challenge,redirect_uri,expires_at)
VALUES ('e4-tenant','00000000-0000-0000-0000-000000000037','e4-state','e4-challenge','https://hezqara.example/callback',now()+interval '10 minutes')
ON CONFLICT DO NOTHING;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM integration_oauth_sessions WHERE clinic_id='e4-tenant' AND state='e4-state') THEN RAISE EXCEPTION 'E4 SMART authorization session missing'; END IF;
  IF EXISTS (SELECT 1 FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname='integration_token_metadata' AND a.attname IN ('access_token','refresh_token')) THEN
    RAISE EXCEPTION 'E4 raw OAuth token column detected';
  END IF;
END $$;
RESET ROLE;
ROLLBACK;
