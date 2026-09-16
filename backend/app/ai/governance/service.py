import json
import uuid
from sqlalchemy import text
from app.ai.governance.contracts import GovernanceDecision, classify_risk

class AIGovernanceService:
    def __init__(self, session, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    async def _clinic_id(self) -> str:
        value = await self.session.scalar(text("select id from clinics where clerk_org_id=:org"), {"org": self.tenant_id})
        if not value:
            raise ValueError("tenant is not mapped to a clinic")
        return str(value)

    async def capabilities(self, limit=50, offset=0):
        clinic = await self._clinic_id()
        r = await self.session.execute(text("select id,name,description,domain,owner,status,risk_tier,phi_classification,approval_required,escalation_required,updated_at from ai_capabilities where clinic_id=:clinic order by id limit :limit offset :offset"), {"clinic": clinic, "limit": limit, "offset": offset})
        return [dict(x._mapping) for x in r]

    async def capability(self, capability_id):
        clinic = await self._clinic_id()
        r = await self.session.execute(text("select * from ai_capabilities where clinic_id=:clinic and id=:id"), {"clinic": clinic, "id": capability_id})
        row = r.mappings().first()
        if not row:
            return None
        v = await self.session.execute(text("select * from ai_capability_versions where clinic_id=:clinic and capability_id=:id order by created_at desc,id desc"), {"clinic": clinic, "id": capability_id})
        return {**dict(row), "versions": [dict(x._mapping) for x in v]}

    async def governance_summary(self):
        clinic = await self._clinic_id()
        q = text("""select count(*) filter(where status='active') active,
        count(*) filter(where status='degraded') degraded,
        count(*) filter(where status='disabled') disabled,
        (select count(*) from ai_execution_telemetry t where t.clinic_id=:clinic and t.created_at>=now()-interval '24 hours') executions,
        (select count(*) from ai_failure_events f where f.clinic_id=:clinic and f.created_at>=now()-interval '24 hours') failures,
        (select count(*) from ai_approvals a where a.clinic_id=:clinic and a.decision='pending') pending_approvals,
        (select count(*) from ai_policy_decisions p where p.clinic_id=:clinic and p.decision='deny' and p.created_at>=now()-interval '24 hours') policy_blocks
        from ai_capabilities where clinic_id=:clinic""")
        r = await self.session.execute(q, {"clinic": clinic})
        return dict(r.mappings().first() or {})

    async def telemetry(self, limit=50, offset=0):
        clinic = await self._clinic_id()
        r = await self.session.execute(text("select execution_id,capability_id,capability_version,workflow_id,workflow_version,provider,model,prompt_version,validation_result,confidence,escalation,approval_required,outcome,failure_category,latency_ms,token_usage,tool_call_count,safety_violation,created_at from ai_execution_telemetry where clinic_id=:clinic order by created_at desc,id desc limit :limit offset :offset"), {"clinic": clinic, "limit": limit, "offset": offset})
        return [dict(x._mapping) for x in r]

    async def trace(self, execution_id):
        clinic = await self._clinic_id()
        t = (await self.session.execute(text("select * from ai_execution_telemetry where clinic_id=:clinic and execution_id=:id order by id desc limit 1"), {"clinic": clinic, "id": execution_id})).mappings().first()
        if not t:
            return None
        p = (await self.session.execute(text("select risk_tier,decision,reason,created_at from ai_policy_decisions where clinic_id=:clinic and execution_id=:id order by created_at desc"), {"clinic": clinic, "id": execution_id})).mappings().all()
        a = (await self.session.execute(text("select id,actor_id,proposed_action,evidence,risk_tier,policy_version,decision,rejection_reason,decided_at from ai_approvals where clinic_id=:clinic and execution_id=:id order by created_at desc"), {"clinic": clinic, "id": execution_id})).mappings().all()
        return {"telemetry": dict(t), "policy_decisions": [dict(x) for x in p], "approvals": [dict(x) for x in a]}

    async def failures(self, limit=50, offset=0):
        clinic = await self._clinic_id()
        r = await self.session.execute(text("select id,execution_id,category,severity,detail,created_at from ai_failure_events where clinic_id=:clinic order by created_at desc,id desc limit :limit offset :offset"), {"clinic": clinic, "limit": limit, "offset": offset})
        return [dict(x._mapping) for x in r]

    async def approvals(self, limit=50, offset=0):
        clinic = await self._clinic_id()
        r = await self.session.execute(text("select id,execution_id,actor_id,proposed_action,evidence,risk_tier,policy_version,decision,rejection_reason,decided_at,created_at from ai_approvals where clinic_id=:clinic order by created_at desc,id desc limit :limit offset :offset"), {"clinic": clinic, "limit": limit, "offset": offset})
        return [dict(x._mapping) for x in r]

    async def controls(self):
        clinic = await self._clinic_id()
        r = await self.session.execute(text("select * from ai_control_state where clinic_id=:clinic"), {"clinic": clinic})
        row = r.mappings().first()
        if row:
            return dict(row)
        await self.session.execute(text("insert into ai_control_state(clinic_id) values(:clinic) on conflict do nothing"), {"clinic": clinic})
        return {"clinic_id": clinic, "ai_enabled": True, "force_human_approval": False, "force_deterministic_fallback": False, "disabled_capabilities": [], "disabled_providers": [], "tool_access_enabled": True}

    async def set_controls(self, payload, actor):
        clinic = await self._clinic_id()
        await self.controls()
        params = {k: payload[k] for k in {"ai_enabled","force_human_approval","force_deterministic_fallback","disabled_capabilities","disabled_providers","tool_access_enabled"} if k in payload}
        params.update({"clinic": clinic, "actor": actor})
        if "disabled_capabilities" in params:
            params["disabled_capabilities"] = json.dumps(params["disabled_capabilities"])
        if "disabled_providers" in params:
            params["disabled_providers"] = json.dumps(params["disabled_providers"])
        await self.session.execute(text("""update ai_control_state set
        ai_enabled=coalesce(:ai_enabled,ai_enabled),
        force_human_approval=coalesce(:force_human_approval,force_human_approval),
        force_deterministic_fallback=coalesce(:force_deterministic_fallback,force_deterministic_fallback),
        disabled_capabilities=coalesce(cast(:disabled_capabilities as jsonb),disabled_capabilities),
        disabled_providers=coalesce(cast(:disabled_providers as jsonb),disabled_providers),
        tool_access_enabled=coalesce(:tool_access_enabled,tool_access_enabled),
        updated_by=:actor,updated_at=now() where clinic_id=:clinic"""), params)
        return await self.controls()

    async def resolve_execution_policy(self, capability_id: str, action: str | None, provider: str | None, confidence: float | None = None, data_classes=(), tools=(), prompt_injection_detected=False, phi_boundary_violation=False) -> GovernanceDecision:
        clinic = await self._clinic_id()
        controls = await self.controls()
        disabled_caps = controls.get("disabled_capabilities") or []
        disabled_providers = controls.get("disabled_providers") or []
        if isinstance(disabled_caps, str): disabled_caps = json.loads(disabled_caps)
        if isinstance(disabled_providers, str): disabled_providers = json.loads(disabled_providers)
        if not controls.get("ai_enabled", True):
            return GovernanceDecision("deny", 0, capability_id, None, None, "AI execution is disabled by governance control", failure_category="POLICY_DENIED")
        if capability_id in disabled_caps:
            return GovernanceDecision("deny", 0, capability_id, None, None, "AI capability is disabled", failure_category="POLICY_DENIED")
        if provider and provider in disabled_providers:
            return GovernanceDecision("deny", 0, capability_id, None, None, "AI provider is disabled", failure_category="POLICY_DENIED")
        cap = (await self.session.execute(text("select * from ai_capabilities where clinic_id=:clinic and id=:id and status='active'"), {"clinic": clinic, "id": capability_id})).mappings().first()
        if not cap:
            return GovernanceDecision("deny", 0, capability_id, None, None, "AI capability is not configured and active", failure_category="POLICY_DENIED")
        version = (await self.session.execute(text("select * from ai_capability_versions where clinic_id=:clinic and capability_id=:id and status='active' order by created_at desc,id desc limit 1"), {"clinic": clinic, "id": capability_id})).mappings().first()
        if not version:
            return GovernanceDecision("deny", int(cap["risk_tier"]), capability_id, None, None, "No active capability version is configured", failure_category="POLICY_DENIED")
        policy = (await self.session.execute(text("select * from ai_policy_versions where clinic_id=:clinic and status='active' order by created_at desc,id desc limit 1"), {"clinic": clinic})).mappings().first()
        if not policy:
            return GovernanceDecision("deny", int(cap["risk_tier"]), capability_id, version["version"], None, "No active AI policy is configured", prompt_version=version["prompt_version"], failure_category="POLICY_DENIED")
        rules = policy.get("rules") or {}
        if not isinstance(rules, dict): rules = {}
        allowed_actions = tuple(cap.get("allowed_actions") or [])
        prohibited_actions = tuple(cap.get("prohibited_actions") or [])
        allowed_data = tuple(cap.get("allowed_data_classes") or [])
        allowed_tools = tuple(version.get("allowed_tools") or [])
        policy_data = tuple(rules.get("allowed_data_classes") or [])
        policy_tools = tuple(rules.get("allowed_tools") or [])
        policy_prohibited = tuple(rules.get("prohibited_actions") or [])
        if policy_data: allowed_data = tuple(x for x in allowed_data if x in policy_data) if allowed_data else policy_data
        if policy_tools: allowed_tools = tuple(x for x in allowed_tools if x in policy_tools) if allowed_tools else policy_tools
        common = dict(risk_tier=int(cap["risk_tier"]), capability_id=capability_id, capability_version=version["version"], policy_version_id=policy["id"], allowed_actions=allowed_actions, allowed_data_classes=allowed_data, allowed_tools=allowed_tools, policy_version=policy["version"], prompt_version=version["prompt_version"], max_output_tokens=int(version["max_output_tokens"]), max_tool_calls=int(version["max_tool_calls"]), max_retries=int(version["max_retries"]), safety_threshold=float(version["safety_threshold"]))
        requested_data = set(data_classes)
        requested_tools = set(tools)
        if prompt_injection_detected: return GovernanceDecision("deny", reason="Prompt injection detected in execution input", failure_category="PROMPT_INJECTION_DETECTED", **common)
        if phi_boundary_violation: return GovernanceDecision("deny", reason="PHI boundary policy violation detected", failure_category="PHI_BOUNDARY_VIOLATION", **common)
        if not controls.get("tool_access_enabled", True) and requested_tools: return GovernanceDecision("deny", reason="Tool access is disabled by governance control", failure_category="TOOL_DENIED", **common)
        if requested_tools and not requested_tools.issubset(set(allowed_tools)): return GovernanceDecision("deny", reason="Requested tool is outside the governance allowlist", failure_category="TOOL_DENIED", **common)
        if requested_data and not requested_data.issubset(set(allowed_data)): return GovernanceDecision("deny", reason="Requested data class is outside the governance allowlist", failure_category="PHI_BOUNDARY_VIOLATION" if "phi" in {x.lower() for x in requested_data} else "POLICY_DENIED", **common)
        if action and (action in prohibited_actions or action in policy_prohibited): return GovernanceDecision("deny", reason="Action is prohibited by capability policy", failure_category="POLICY_DENIED", **common)
        if allowed_actions and action and action not in allowed_actions: return GovernanceDecision("deny", reason="Action is outside the capability allowlist", failure_category="POLICY_DENIED", **common)
        if provider:
            health = (await self.session.execute(text("select status from ai_provider_health where clinic_id=:clinic and provider=:provider order by checked_at desc limit 1"), {"clinic": clinic, "provider": provider})).scalar()
            if health in {"unavailable", "not_configured"}: return GovernanceDecision("deny", reason="AI provider is unavailable or not configured", failure_category="MODEL_UNAVAILABLE", **common)
            if health == "rate_limited": return GovernanceDecision("escalate", reason="AI provider is rate limited", escalation_required=True, failure_category="RATE_LIMITED", **common)
            if health == "degraded": return GovernanceDecision("escalate", reason="AI provider is degraded", escalation_required=True, failure_category="MODEL_UNAVAILABLE", **common)
        decision = classify_risk(int(cap["risk_tier"]), action, bool(cap["approval_required"]) or bool(controls.get("force_human_approval")) or bool(rules.get("approval_required")))
        if confidence is not None and confidence < float(version["quality_threshold"]):
            return GovernanceDecision("escalate", reason="Confidence is below the configured quality threshold", escalation_required=True, failure_category="CONFIDENCE_TOO_LOW", **common)
        return GovernanceDecision(decision.decision, reason=decision.reason, approval_required=decision.decision == "approval_required", escalation_required=bool(cap["escalation_required"]), **common)

    async def record_policy(self, execution_id, policy, action):
        clinic = await self._clinic_id()
        d = classify_risk(int(policy.risk_tier), action, policy.approval_required)
        await self.session.execute(text("insert into ai_policy_decisions(id,clinic_id,execution_id,policy_version_id,risk_tier,decision,reason) values(:id,:clinic,:execution,:policy,:risk,:decision,:reason)"), {"id": str(uuid.uuid4()), "clinic": clinic, "execution": execution_id, "policy": getattr(policy, "policy_version_id", None), "risk": int(d.risk_tier), "decision": d.decision, "reason": d.reason})
        return d
