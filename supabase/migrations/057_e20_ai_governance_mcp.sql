CREATE TABLE IF NOT EXISTS ai_tool_policies (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 tool_key TEXT NOT NULL,
 interface_type TEXT NOT NULL CHECK(interface_type IN ('mcp','native','fhir','rest')),
 risk_tier integer NOT NULL CHECK(risk_tier BETWEEN 0 AND 5),
 tenant_scoped BOOLEAN NOT NULL DEFAULT true,
 side_effect BOOLEAN NOT NULL DEFAULT false,
 approval_required BOOLEAN NOT NULL DEFAULT false,
 idempotent BOOLEAN NOT NULL DEFAULT true,
 allowed_data_classes JSONB NOT NULL DEFAULT '[]'::jsonb,
 allowed_actions JSONB NOT NULL DEFAULT '[]'::jsonb,
 status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','disabled')),
 version TEXT NOT NULL DEFAULT 'e20.v1',
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 CONSTRAINT ai_tool_policies_clinic_id_uidx UNIQUE(clinic_id,id),
 CONSTRAINT ai_tool_policies_key_uk UNIQUE(clinic_id,tool_key)
);
ALTER TABLE ai_tool_policies ENABLE ROW LEVEL SECURITY; ALTER TABLE ai_tool_policies FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS ai_tool_policies_isolation ON ai_tool_policies;
CREATE POLICY ai_tool_policies_isolation ON ai_tool_policies USING(clinic_id IN(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK(clinic_id IN(SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
GRANT SELECT,INSERT,UPDATE,DELETE ON ai_tool_policies TO authenticated;
CREATE INDEX IF NOT EXISTS idx_ai_tool_policies_active ON ai_tool_policies(clinic_id,status,risk_tier);
