import json,uuid
from datetime import datetime,timezone
from sqlalchemy import text
from app.ai.governance.contracts import CapabilityPolicy,RiskTier,classify_risk,score_case

class AIGovernanceService:
    def __init__(self,session,tenant_id:str): self.session=session; self.tenant_id=tenant_id
    async def capabilities(self,limit:int=50,offset:int=0):
        q=text("select id,name,description,domain,owner,status,risk_tier,phi_classification,approval_required,escalation_required,updated_at from ai_capabilities where clinic_id=:tenant order by id limit :limit offset :offset")
        r=await self.session.execute(q,{'tenant':self.tenant_id,'limit':limit,'offset':offset}); return [dict(x._mapping) for x in r]
    async def capability(self,capability_id:str):
        r=await self.session.execute(text("select * from ai_capabilities where clinic_id=:tenant and id=:id"),{'tenant':self.tenant_id,'id':capability_id}); row=r.mappings().first()
        if not row:return None
        v=await self.session.execute(text("select * from ai_capability_versions where clinic_id=:tenant and capability_id=:id order by created_at desc"),{'tenant':self.tenant_id,'id':capability_id})
        return {**dict(row),'versions':[dict(x._mapping) for x in v]}
    async def governance_summary(self):
        q=text("""select count(*) filter(where status='active') active,count(*) filter(where status='degraded') degraded,count(*) filter(where status='disabled') disabled,
        (select count(*) from ai_execution_telemetry t where t.clinic_id=:tenant and t.created_at>=now()-interval '24 hours') executions,
        (select count(*) from ai_failure_events f where f.clinic_id=:tenant and f.created_at>=now()-interval '24 hours') failures,
        (select count(*) from ai_approvals a where a.clinic_id=:tenant and a.decision='pending') pending_approvals,
        (select count(*) from ai_policy_decisions p where p.clinic_id=:tenant and p.decision='deny' and p.created_at>=now()-interval '24 hours') policy_blocks
        from ai_capabilities where clinic_id=:tenant""")
        r=await self.session.execute(q,{'tenant':self.tenant_id}); return dict(r.mappings().first() or {})
    async def telemetry(self,limit:int=50,offset:int=0):
        r=await self.session.execute(text("select execution_id,capability_id,capability_version,workflow_id,workflow_version,provider,model,prompt_version,validation_result,confidence,escalation,approval_required,outcome,failure_category,latency_ms,token_usage,tool_call_count,safety_violation,created_at from ai_execution_telemetry where clinic_id=:tenant order by created_at desc,id desc limit :limit offset :offset"),{'tenant':self.tenant_id,'limit':limit,'offset':offset}); return [dict(x._mapping) for x in r]
    async def failures(self,limit:int=50,offset:int=0):
        r=await self.session.execute(text("select id,execution_id,category,severity,detail,created_at from ai_failure_events where clinic_id=:tenant order by created_at desc,id desc limit :limit offset :offset"),{'tenant':self.tenant_id,'limit':limit,'offset':offset}); return [dict(x._mapping) for x in r]
    async def approvals(self,limit:int=50,offset:int=0):
        r=await self.session.execute(text("select id,execution_id,actor_id,proposed_action,evidence,risk_tier,policy_version,decision,rejection_reason,decided_at,created_at from ai_approvals where clinic_id=:tenant order by created_at desc limit :limit offset :offset"),{'tenant':self.tenant_id,'limit':limit,'offset':offset}); return [dict(x._mapping) for x in r]
    async def controls(self):
        r=await self.session.execute(text("select * from ai_control_state where clinic_id=:tenant"),{'tenant':self.tenant_id}); row=r.mappings().first()
        if row:return dict(row)
        await self.session.execute(text("insert into ai_control_state(clinic_id) values(:tenant) on conflict do nothing"),{'tenant':self.tenant_id})
        return {'clinic_id':self.tenant_id,'ai_enabled':True,'force_human_approval':False,'force_deterministic_fallback':False,'disabled_capabilities':[],'disabled_providers':[],'tool_access_enabled':True}
    async def set_controls(self,payload:dict,actor:str):
        current=await self.controls(); allowed={'ai_enabled','force_human_approval','force_deterministic_fallback','disabled_capabilities','disabled_providers','tool_access_enabled'}
        values={k:payload[k] for k in allowed if k in payload}; values['tenant']=self.tenant_id; values['actor']=actor
        await self.session.execute(text("""update ai_control_state set ai_enabled=coalesce(:ai_enabled,ai_enabled),force_human_approval=coalesce(:force_human_approval,force_human_approval),force_deterministic_fallback=coalesce(:force_deterministic_fallback,force_deterministic_fallback),disabled_capabilities=coalesce(cast(:disabled_capabilities as jsonb),disabled_capabilities),disabled_providers=coalesce(cast(:disabled_providers as jsonb),disabled_providers),tool_access_enabled=coalesce(:tool_access_enabled,tool_access_enabled),updated_by=:actor,updated_at=now() where clinic_id=:tenant"""),{**values,'disabled_capabilities':json.dumps(values['disabled_capabilities']) if 'disabled_capabilities' in values else None,'disabled_providers':json.dumps(values['disabled_providers']) if 'disabled_providers' in values else None})
        return await self.controls()
    async def record_policy(self,execution_id:str,policy:CapabilityPolicy,action:str|None):
        d=classify_risk(int(policy.risk_tier),action,policy.approval_required)
        await self.session.execute(text("insert into ai_policy_decisions(id,clinic_id,execution_id,risk_tier,decision,reason) values(:id,:tenant,:execution,:risk,:decision,:reason)"),{'id':str(uuid.uuid4()),'tenant':self.tenant_id,'execution':execution_id,'risk':int(d.risk_tier),'decision':d.decision,'reason':d.reason})
        return d
