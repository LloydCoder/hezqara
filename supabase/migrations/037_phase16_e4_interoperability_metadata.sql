-- E4: production interoperability metadata and SMART authorization session state.
CREATE TABLE IF NOT EXISTS integration_oauth_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id text NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
  integration_id uuid NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
  state text NOT NULL,
  code_challenge text NOT NULL,
  code_challenge_method text NOT NULL DEFAULT 'S256' CHECK (code_challenge_method='S256'),
  nonce text,
  requested_scopes text[] NOT NULL DEFAULT '{}',
  launch_context jsonb NOT NULL DEFAULT '{}'::jsonb,
  redirect_uri text NOT NULL,
  expires_at timestamptz NOT NULL,
  used_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(clinic_id,state)
);
CREATE TABLE IF NOT EXISTS integration_token_metadata (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id text NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
  integration_id uuid NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
  credential_ref text NOT NULL,
  token_type text NOT NULL DEFAULT 'Bearer',
  scopes text[] NOT NULL DEFAULT '{}',
  issued_at timestamptz,
  expires_at timestamptz,
  last_refreshed_at timestamptz,
  status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','expired','revoked','refresh_required')),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(integration_id,credential_ref)
);
CREATE TABLE IF NOT EXISTS integration_protocol_capabilities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id text NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
  integration_id uuid NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
  protocol text NOT NULL,
  version text NOT NULL,
  supported boolean NOT NULL DEFAULT true,
  configuration jsonb NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE(integration_id,protocol,version)
);

ALTER TABLE integrations ADD COLUMN IF NOT EXISTS fhir_version text DEFAULT '4.0.1';
ALTER TABLE integrations ADD COLUMN IF NOT EXISTS smart_version text;
ALTER TABLE integrations ADD COLUMN IF NOT EXISTS auth_method text CHECK (auth_method IS NULL OR auth_method IN ('smart_public_pkce','smart_confidential','backend_service'));

CREATE INDEX IF NOT EXISTS integration_oauth_sessions_expiry_idx ON integration_oauth_sessions(expires_at) WHERE used_at IS NULL;
CREATE INDEX IF NOT EXISTS integration_token_metadata_expiry_idx ON integration_token_metadata(expires_at,status);
CREATE INDEX IF NOT EXISTS integration_protocol_capabilities_idx ON integration_protocol_capabilities(clinic_id,integration_id,protocol);

DO $$ DECLARE t text; BEGIN
 FOR t IN SELECT unnest(ARRAY['integration_oauth_sessions','integration_token_metadata','integration_protocol_capabilities']) LOOP
  EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',t);
  EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY',t);
  EXECUTE format('DROP POLICY IF EXISTS e4_tenant_boundary ON public.%I',t);
  EXECUTE format('CREATE POLICY e4_tenant_boundary ON public.%I AS RESTRICTIVE FOR ALL TO authenticated USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true))) WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting(''app.clerk_org_id'',true)))',t);
  EXECUTE format('REVOKE ALL ON public.%I FROM anon',t);
 END LOOP;
END $$;
