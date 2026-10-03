CREATE TABLE IF NOT EXISTS integration_connections (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 provider_key TEXT NOT NULL,
 interface_type TEXT NOT NULL CHECK(interface_type IN ('fhir','smart','payer_api','payment','messaging','document')),
 environment TEXT NOT NULL CHECK(environment IN ('sandbox','production')),
 endpoint TEXT,
 auth_scheme TEXT,
 supported_resources JSONB NOT NULL DEFAULT '[]'::jsonb,
 status TEXT NOT NULL DEFAULT 'not_verified' CHECK(status IN ('not_verified','healthy','degraded','failed','disabled')),
 last_verified_at TIMESTAMPTZ,
 failure_class TEXT,
 metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 CONSTRAINT integration_connections_clinic_id_uidx UNIQUE(clinic_id,id), CONSTRAINT integration_connections_key_uk UNIQUE(clinic_id,provider_key,interface_type,environment)
);
ALTER TABLE integration_connections ENABLE ROW LEVEL SECURITY; ALTER TABLE integration_connections FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS integration_connections_isolation ON integration_connections;
CREATE POLICY integration_connections_isolation ON integration_connections USING(clinic_id IN(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK(clinic_id IN(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
GRANT SELECT,INSERT,UPDATE,DELETE ON integration_connections TO authenticated;
CREATE INDEX IF NOT EXISTS idx_integration_connections_status ON integration_connections(clinic_id,status,last_verified_at DESC);
