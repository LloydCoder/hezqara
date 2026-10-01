-- Phase 9: AI reliability, evaluation and governance.
-- Tenant-scoped, append-oriented records. No PHI payloads are required by this schema.
CREATE TABLE IF NOT EXISTS ai_capabilities (
 id TEXT NOT NULL, clinic_id TEXT NOT NULL, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', domain TEXT NOT NULL, owner TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','degraded','disabled','review')),
 risk_tier SMALLINT NOT NULL CHECK (risk_tier BETWEEN 0 AND 4), phi_classification TEXT NOT NULL DEFAULT 'operational',
 allowed_data_classes JSONB NOT NULL DEFAULT '[]', allowed_actions JSONB NOT NULL DEFAULT '[]', prohibited_actions JSONB NOT NULL DEFAULT '[]',
 approval_required BOOLEAN NOT NULL DEFAULT false, escalation_required BOOLEAN NOT NULL DEFAULT false,
 disabled_reason TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 PRIMARY KEY (clinic_id,id)
);
CREATE TABLE IF NOT EXISTS ai_capability_versions (
 id BIGSERIAL PRIMARY KEY, clinic_id TEXT NOT NULL, capability_id TEXT NOT NULL, version TEXT NOT NULL,
 model_provider TEXT, model_version TEXT, prompt_version TEXT NOT NULL, system_instruction_version TEXT NOT NULL,
 tool_policy_version TEXT NOT NULL, output_schema_version TEXT NOT NULL, evaluation_suite_version TEXT,
 timeout_ms INTEGER NOT NULL DEFAULT 30000 CHECK (timeout_ms BETWEEN 100 AND 300000), max_output_tokens INTEGER NOT NULL DEFAULT 2048 CHECK (max_output_tokens BETWEEN 1 AND 32768),
 max_tool_calls INTEGER NOT NULL DEFAULT 0 CHECK (max_tool_calls BETWEEN 0 AND 100), max_retries INTEGER NOT NULL DEFAULT 1 CHECK (max_retries BETWEEN 0 AND 5),
 quality_threshold NUMERIC(5,4) NOT NULL DEFAULT 0.8000 CHECK (quality_threshold BETWEEN 0 AND 1), safety_threshold NUMERIC(5,4) NOT NULL DEFAULT 1.0000 CHECK (safety_threshold BETWEEN 0 AND 1),
 input_schema JSONB NOT NULL DEFAULT '{}', output_schema JSONB NOT NULL DEFAULT '{}', allowed_tools JSONB NOT NULL DEFAULT '[]',
 status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('draft','active','retired','disabled')), created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE (clinic_id,capability_id,version), FOREIGN KEY (clinic_id,capability_id) REFERENCES ai_capabilities(clinic_id,id)
);
CREATE TABLE IF NOT EXISTS ai_evaluation_suites (
 id BIGSERIAL PRIMARY KEY, clinic_id TEXT NOT NULL, capability_id TEXT NOT NULL, version TEXT NOT NULL, name TEXT NOT NULL,
 description TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('draft','active','retired')),
 quality_threshold NUMERIC(5,4) NOT NULL DEFAULT 0.8000 CHECK (quality_threshold BETWEEN 0 AND 1), safety_threshold NUMERIC(5,4) NOT NULL DEFAULT 1 CHECK (safety_threshold BETWEEN 0 AND 1),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(clinic_id,capability_id,version), FOREIGN KEY (clinic_id,capability_id) REFERENCES ai_capabilities(clinic_id,id)
);
CREATE TABLE IF NOT EXISTS ai_evaluation_cases (
 id BIGSERIAL PRIMARY KEY, clinic_id TEXT NOT NULL, suite_id BIGINT NOT NULL REFERENCES ai_evaluation_suites(id), case_key TEXT NOT NULL,
 dataset_version TEXT NOT NULL, category TEXT NOT NULL, input JSONB NOT NULL, expected JSONB NOT NULL, constraints JSONB NOT NULL DEFAULT '{}', synthetic_only BOOLEAN NOT NULL DEFAULT true,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(clinic_id,suite_id,case_key)
);
CREATE TABLE IF NOT EXISTS ai_evaluation_runs (
 id UUID PRIMARY KEY, clinic_id TEXT NOT NULL, suite_id BIGINT NOT NULL REFERENCES ai_evaluation_suites(id), capability_version_id BIGINT REFERENCES ai_capability_versions(id),
 model_provider TEXT, model_version TEXT, prompt_version TEXT, status TEXT NOT NULL CHECK(status IN ('queued','running','completed','failed')),
 pass_rate NUMERIC(6,5), safety_rate NUMERIC(6,5), started_at TIMESTAMPTZ, completed_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS ai_evaluation_results (
 id BIGSERIAL PRIMARY KEY, clinic_id TEXT NOT NULL, run_id UUID NOT NULL REFERENCES ai_evaluation_runs(id), case_id BIGINT NOT NULL REFERENCES ai_evaluation_cases(id),
 passed BOOLEAN NOT NULL, safety_passed BOOLEAN NOT NULL, score NUMERIC(6,5), latency_ms INTEGER, token_usage INTEGER, failure_category TEXT,
 observed JSONB NOT NULL DEFAULT '{}', evidence JSONB NOT NULL DEFAULT '[]', created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS ai_policy_versions (
 id BIGSERIAL PRIMARY KEY, clinic_id TEXT NOT NULL, version TEXT NOT NULL, rules JSONB NOT NULL, status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('draft','active','retired')),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(clinic_id,version)
);
CREATE TABLE IF NOT EXISTS ai_policy_decisions (
 id UUID PRIMARY KEY, clinic_id TEXT NOT NULL, execution_id TEXT NOT NULL, policy_version_id BIGINT REFERENCES ai_policy_versions(id), decision TEXT NOT NULL CHECK(decision IN ('allow','deny','approval_required','escalate')),
 risk_tier SMALLINT NOT NULL CHECK(risk_tier BETWEEN 0 AND 4), reason TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS ai_execution_telemetry (
 id BIGSERIAL PRIMARY KEY, clinic_id TEXT NOT NULL, execution_id TEXT NOT NULL, capability_id TEXT NOT NULL, capability_version TEXT NOT NULL,
 workflow_id TEXT, workflow_version TEXT, request_id TEXT, provider TEXT, model TEXT, prompt_version TEXT, validation_result TEXT,
 confidence NUMERIC(6,5), escalation BOOLEAN NOT NULL DEFAULT false, approval_required BOOLEAN NOT NULL DEFAULT false, outcome TEXT, failure_category TEXT,
 latency_ms INTEGER, token_usage INTEGER, tool_call_count INTEGER NOT NULL DEFAULT 0, safety_violation BOOLEAN NOT NULL DEFAULT false,
 input_provenance JSONB NOT NULL DEFAULT '{}', created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS ai_failure_events (
 id BIGSERIAL PRIMARY KEY, clinic_id TEXT NOT NULL, execution_id TEXT, category TEXT NOT NULL, severity TEXT NOT NULL DEFAULT 'medium' CHECK(severity IN ('low','medium','high','critical')),
 detail TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS ai_approvals (
 id UUID PRIMARY KEY, clinic_id TEXT NOT NULL, execution_id TEXT NOT NULL, actor_id TEXT, proposed_action JSONB NOT NULL, evidence JSONB NOT NULL DEFAULT '[]',
 risk_tier SMALLINT NOT NULL CHECK(risk_tier BETWEEN 0 AND 4), policy_version TEXT NOT NULL, decision TEXT NOT NULL DEFAULT 'pending' CHECK(decision IN ('pending','approved','rejected')),
 rejection_reason TEXT, decided_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS ai_provider_health (
 id BIGSERIAL PRIMARY KEY, clinic_id TEXT NOT NULL, provider TEXT NOT NULL, model TEXT, status TEXT NOT NULL CHECK(status IN ('healthy','degraded','unavailable','rate_limited','not_configured')),
 latency_ms INTEGER, error_category TEXT, checked_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(clinic_id,provider,model)
);
CREATE TABLE IF NOT EXISTS ai_control_state (
 clinic_id TEXT PRIMARY KEY, ai_enabled BOOLEAN NOT NULL DEFAULT true, force_human_approval BOOLEAN NOT NULL DEFAULT false,
 force_deterministic_fallback BOOLEAN NOT NULL DEFAULT false, disabled_capabilities JSONB NOT NULL DEFAULT '[]', disabled_providers JSONB NOT NULL DEFAULT '[]', tool_access_enabled BOOLEAN NOT NULL DEFAULT true,
 updated_by TEXT, updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_capabilities_clinic_status ON ai_capabilities(clinic_id,status);
CREATE INDEX IF NOT EXISTS idx_ai_cap_versions_clinic_cap ON ai_capability_versions(clinic_id,capability_id,status);
CREATE INDEX IF NOT EXISTS idx_ai_eval_cases_clinic_suite ON ai_evaluation_cases(clinic_id,suite_id);
CREATE INDEX IF NOT EXISTS idx_ai_eval_runs_clinic_created ON ai_evaluation_runs(clinic_id,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_eval_results_clinic_run ON ai_evaluation_results(clinic_id,run_id,created_at);
CREATE INDEX IF NOT EXISTS idx_ai_telemetry_clinic_created ON ai_execution_telemetry(clinic_id,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_failures_clinic_created ON ai_failure_events(clinic_id,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_approvals_clinic_decision ON ai_approvals(clinic_id,decision,created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_provider_health_clinic ON ai_provider_health(clinic_id,status);

DO $$ DECLARE t TEXT; BEGIN FOR t IN SELECT unnest(ARRAY['ai_capabilities','ai_capability_versions','ai_evaluation_suites','ai_evaluation_cases','ai_evaluation_runs','ai_evaluation_results','ai_policy_versions','ai_policy_decisions','ai_execution_telemetry','ai_failure_events','ai_approvals','ai_provider_health','ai_control_state']) LOOP EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY',t); EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY',t); EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON %I TO authenticated',t); END LOOP; END $$;
CREATE POLICY ai_capabilities_tenant ON ai_capabilities USING (clinic_id=current_setting('app.clerk_org_id',true)) WITH CHECK (clinic_id=current_setting('app.clerk_org_id',true));
CREATE POLICY ai_capability_versions_tenant ON ai_capability_versions USING (clinic_id=current_setting('app.clerk_org_id',true)) WITH CHECK (clinic_id=current_setting('app.clerk_org_id',true));
CREATE POLICY ai_evaluation_suites_tenant ON ai_evaluation_suites USING (clinic_id=current_setting('app.clerk_org_id',true)) WITH CHECK (clinic_id=current_setting('app.clerk_org_id',true));
CREATE POLICY ai_evaluation_cases_tenant ON ai_evaluation_cases USING (clinic_id=current_setting('app.clerk_org_id',true)) WITH CHECK (clinic_id=current_setting('app.clerk_org_id',true));
CREATE POLICY ai_evaluation_runs_tenant ON ai_evaluation_runs USING (clinic_id=current_setting('app.clerk_org_id',true)) WITH CHECK (clinic_id=current_setting('app.clerk_org_id',true));
CREATE POLICY ai_evaluation_results_tenant ON ai_evaluation_results USING (clinic_id=current_setting('app.clerk_org_id',true)) WITH CHECK (clinic_id=current_setting('app.clerk_org_id',true));
CREATE POLICY ai_policy_versions_tenant ON ai_policy_versions USING (clinic_id=current_setting('app.clerk_org_id',true)) WITH CHECK (clinic_id=current_setting('app.clerk_org_id',true));
CREATE POLICY ai_policy_decisions_tenant ON ai_policy_decisions USING (clinic_id=current_setting('app.clerk_org_id',true)) WITH CHECK (clinic_id=current_setting('app.clerk_org_id',true));
CREATE POLICY ai_execution_telemetry_tenant ON ai_execution_telemetry USING (clinic_id=current_setting('app.clerk_org_id',true)) WITH CHECK (clinic_id=current_setting('app.clerk_org_id',true));
CREATE POLICY ai_failure_events_tenant ON ai_failure_events USING (clinic_id=current_setting('app.clerk_org_id',true)) WITH CHECK (clinic_id=current_setting('app.clerk_org_id',true));
CREATE POLICY ai_approvals_tenant ON ai_approvals USING (clinic_id=current_setting('app.clerk_org_id',true)) WITH CHECK (clinic_id=current_setting('app.clerk_org_id',true));
CREATE POLICY ai_provider_health_tenant ON ai_provider_health USING (clinic_id=current_setting('app.clerk_org_id',true)) WITH CHECK (clinic_id=current_setting('app.clerk_org_id',true));
CREATE POLICY ai_control_state_tenant ON ai_control_state USING (clinic_id=current_setting('app.clerk_org_id',true)) WITH CHECK (clinic_id=current_setting('app.clerk_org_id',true));
GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;
