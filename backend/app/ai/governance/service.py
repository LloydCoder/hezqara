import json,uuid
from sqlalchemy import text
from app.ai.governance.contracts import GovernanceDecision,classify_risk

class AIGovernanceService:
    def __init__(self,session,tenant_id:str):self.session=session;self.tenant_id=tenant_id
    async def capabilities(self,limit=50,offset=0):
        r=await self.session.execute(text("select id,name,description,domain,owner,status,risk_tier,phi_classification,approval_required,escalation_required,updated_at from ai_capabilities where clinic_id=:tenant order by id limit :limit offset :offset"),{'tenant':self.tenant_id,'limit':limit,'offset':offset});return [dict(x._mapping) for x in r]
    async def capability(self,capability_id):
        r=await self.session.execute(text("select * from ai_capabilities where clinic_id=:tenant and id=:id"),{'tenant':self.tenant_id,'id':capability_id});row=r.mappings().first()
        if not row:return None
        v=await self.session.execute(text("select * from ai_capability_versions where clinic_id=:tenant and capability_id=:id order by created_at desc"),{'tenant':self.tenant_id,'id':capability_id});return {**dict(row),'versions':[dict(x._mapping) for x in v]}
    async def governance_summary(self):
        q=text("""select count(*) filter(where status='active') active,count(*) filter(where status='degraded') degraded,count(*) filter(where status='disabled') disabled,
        (select count(*) from ai_execution_telemetry t where t.clinic_id=:tenant and t.created_at>=now()-interval '24 hours') executions,
        (select count(*) from ai_failure_events f where f.clinic_id=:tenant and f.created_at>=now()-interval '24 hours') failures,
        (select count(*) from ai_approvals a where a.clinic_id=:tenant and a.decision='pending') pending_approvals,
        (select count(*) from ai_policy_decisions p where p.clinic_id=:tenant and p.decision='deny' and p.created_at>=now()-interval '24 hours') policy_blocks
        from ai_capabilities where clinic_id=:tenant""");r=await self.session.execute(q,{'tenant':self.tenant_id});return dict(r.mappings().first() or {})
    async def telemetry(self,limit=50,offset=0):
        r=await self.session.execute(text("select execution_id,capability_id,capability_version,workflow_id,workflow_version,provider,model,prompt_version,validation_result,confidence,escalation,approval_required,outcome,failure_category,latency_ms,token_usage,tool_call_count,safety_violation,created_at from ai_execution_telemetry where clinic_id=:tenant order by created_at desc,id desc limit :limit offset :offset"),{'tenant':self.tenant_id,'limit':limit,'offset':offset});return [dict(x._mapping) for x in r]
    async def trace(self,execution_id):
        t=(await self.session.execute(text("select * from ai_execution_telemetry where clinic_id=:tenant and execution_id=:id order by id desc limit 1"),{'tenant':self.tenant_id,'id':execution_id})).mappings().first();p=(await self.session.execute(text("select risk_tier,decision,reason,created_at from ai_policy_decisions where clinic_id=:tenant and execution_id=:id order by created_at desc"),{'tenant':self.tenant_id,'id':execution_id})).mappings().all();a=(await self.session.execute(text("select id,actor_id,proposed_action,evidence,risk_tier,policy_version,decision,rejection_reason,decided_at from ai_approvals where clinic_id=:tenant and execution_id=:id order by created_at desc"),{'tenant':self.tenant_id,'id':execution_id})).mappings().all()
        if not t:return None
        return {'telemetry':dict(t),'policy_decisions':[dict(x) for x in p],'approvals':[dict(x) for x in a]}
    async def failures(self,limit=50,offset=0):
        r=await self.session.execute(text("select id,execution_id,category,severity,detail,created_at from ai_failure_events where clinic_id=:tenant order by created_at desc,id desc limit :limit offset :offset"),{'tenant':self.tenant_id,'limit':limit,'offset':offset});return [dict(x._mapping) for x in r]
    async def approvals(self,limit=50,offset=0):
        r=await self.session.execute(text("select id,execution_id,actor_id,proposed_action,evidence,risk_tier,policy_version,decision,rejection_reason,decided_at,created_at from ai_approvals where clinic_id=:tenant order by created_at desc limit :limit offset :offset"),{'tenant':self.tenant_id,'limit':limit,'offset':offset});return [dict(x._mapping) for x in r]
    async def controls(self):
        r=await self.session.execute(text("select * from ai_control_state where clinic_id=:tenant"),{'tenant':self.tenant_id});row=r.mappings().first()
        if row:return dict(row)
        await self.session.execute(text("insert into ai_control_state(clinic_id) values(:tenant) on conflict do nothing"),{'tenant':self.tenant_id});return {'clinic_id':self.tenant_id,'ai_enabled':True,'force_human_approval':False,'force_deterministic_fallback':False,'disabled_capabilities':[],'disabled_providers':[],'tool_access_enabled':True}
    async def set_controls(self,payload,actor):
        await self.controls();v={k:payload[k] for k in {'ai_enabled','force_human_approval','force_deterministic_fallback','disabled_capabilities','disabled_providers','tool_access_enabled'} if k in payload};v.update({'tenant':self.tenant_id,'actor':actor,'disabled_capabilities':json.dumps(v['disabled_capabilities']) if 'disabled_capabilities' in v else None,'disabled_providers':json.dumps(v['disabled_providers']) if 'disabled_providers' in v else None})
        await self.session.execute(text("update ai_control_state set ai_enabled=coalesce(:ai_enabled,ai_enabled),force_human_approval=coalesce(:force_human_approval,force_human_approval),force_deterministic_fallback=coalesce(:force_deterministic_fallback,force_deterministic_fallback),disabled_capabilities=coalesce(cast(:disabled_capabilities as jsonb),disabled_capabilities),disabled_providers=coalesce(cast(:disabled_providers as jsonb),disabled_providers),tool_access_enabled=coalesce(:tool_access_enabled,tool_access_enabled),updated_by=:actor,updated_at=now() where clinic_id=:tenant"),v);return await self.controls()
    async def resolve_execution_policy(self,capability_id:str,action:str|None,provider:str|None,confidence:float|None=None)->GovernanceDecision:
        controls=await self.controls();disabled_caps=controls.get('disabled_capabilities') or [];disabled_providers=controls.get('disabled_providers') or []
        if isinstance(disabled_caps,str):disabled_caps=json.loads(disabled_caps)
        if isinstance(disabled_providers,str):disabled_providers=json.loads(disabled_providers)
        if not controls.get('ai_enabled',True):return GovernanceDecision(decision='deny',risk_tier=0,capability_id=capability_id,capability_version=None,policy_version_id=None,reason='AI execution is disabled by governance control',failure_category='POLICY_DENIED')
        if capability_id in disabled_caps:return GovernanceDecision(decision='deny',risk_tier=0,capability_id=capability_id,capability_version=None,policy_version_id=None,reason='AI capability is disabled',failure_category='POLICY_DENIED')
        if provider and provider in disabled_providers:return GovernanceDecision(decision='deny',risk_tier=0,capability_id=capability_id,capability_version=None,policy_version_id=None,reason='AI provider is disabled',failure_category='POLICY_DENIED')
        cap=(await self.session.execute(text("select * from ai_capabilities where clinic_id=:tenant and id=:id and status='active'"),{'tenant':self.tenant_id,'id':capability_id})).mappings().first()
        if not cap:return GovernanceDecision(decision='deny',risk_tier=0,capability_id=capability_id,capability_version=None,policy_version_id=None,reason='AI capability is not configured and active',failure_category='POLICY_DENIED')
        version=(await self.session.execute(text("select * from ai_capability_versions where clinic_id=:tenant and capability_id=:id and status='active' order by created_at desc,id desc limit 1"),{'tenant':self.tenant_id,'id':capability_id})).mappings().first()
        if not version:return GovernanceDecision(decision='deny',risk_tier=int(cap['risk_tier']),capability_id=capability_id,capability_version=None,policy_version_id=None,reason='No active capability version is configured',failure_category='POLICY_DENIED')
        policy=(await self.session.execute(text("select * from ai_policy_versions where clinic_id=:tenant and status='active' order by created_at desc,id desc limit 1"),{'tenant':self.tenant_id})).mappings().first()
        if not policy:return GovernanceDecision(decision='deny',risk_tier=int(cap['risk_tier']),capability_id=capability_id,capability_version=version['version'],policy_version_id=None,reason='No active AI policy is configured',prompt_version=version['prompt_version'],failure_category='POLICY_DENIED')
        allowed_actions=tuple(cap.get('allowed_actions') or []);prohibited_actions=tuple(cap.get('prohibited_actions') or []);allowed_data=tuple(cap.get('allowed_data_classes') or []);allowed_tools=tuple(version.get('allowed_tools') or [])
        common=dict(risk_tier=int(cap['risk_tier']),capability_id=capability_id,capability_version=version['version'],policy_version_id=policy['id'],allowed_actions=allowed_actions,allowed_data_classes=allowed_data,allowed_tools=allowed_tools,policy_version=policy['version'],prompt_version=version['prompt_version'])
        if action and action in prohibited_actions:return GovernanceDecision(decision='deny',reason='Action is prohibited by capability policy',failure_category='POLICY_DENIED',**common)
        if allowed_actions and action and action not in allowed_actions:return GovernanceDecision(decision='deny',reason='Action is outside the capability allowlist',failure_category='POLICY_DENIED',**common)
        decision=classify_risk(int(cap['risk_tier']),action,bool(cap['approval_required']) or bool(controls.get('force_human_approval')))
        if confidence is not None and confidence < float(version['quality_threshold']):return GovernanceDecision(decision='escalate',reason='Confidence is below the configured quality threshold',escalation_required=True,failure_category='CONFIDENCE_TOO_LOW',**common)
        return GovernanceDecision(decision=decision.decision,reason=decision.reason,approval_required=decision.decision=='approval_required',escalation_required=bool(cap['escalation_required']),**common)
    async def record_policy(self,execution_id,policy,action):
        d=classify_risk(int(policy.risk_tier),action,policy.approval_required);await self.session.execute(text("insert into ai_policy_decisions(id,clinic_id,execution_id,policy_version_id,risk_tier,decision,reason) values(:id,:tenant,:execution,:policy,:risk,:decision,:reason)"),{'id':str(uuid.uuid4()),'tenant':self.tenant_id,'execution':execution_id,'policy':getattr(policy,'policy_version_id',None),'risk':int(d.risk_tier),'decision':d.decision,'reason':d.reason});return d
