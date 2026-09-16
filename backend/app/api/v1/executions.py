from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
import json, uuid
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.security.audit import append_event
from app.workforce.base.contracts import AgentContext, AgentRequest
from app.workforce.registry import registry
from app.domains.executions.repository import ExecutionRepository
from app.ai.governance.contracts import validate_output
from app.ai.governance.service import AIGovernanceService
from app.ai.guardrails.policy import classify_input_data_classes, detect_phi_boundary_violation, detect_prompt_injection

router = APIRouter(prefix='/executions', tags=['executions'])

class ExecutionRequest(BaseModel):
    agent_type: str = Field(min_length=1, max_length=100)
    task: str = Field(min_length=1, max_length=500)
    input: dict = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=8, max_length=200)
    data_classes: list[str] = Field(default_factory=list, max_length=20)
    tools: list[str] = Field(default_factory=list, max_length=50)

@router.get('')
async def list_executions(limit: int = 50, offset: int = 0, tenant: TenantContext = Depends(require_permission('executions:read'))):
    if limit < 1 or limit > 100 or offset < 0:
        raise HTTPException(status_code=400, detail='invalid pagination')
    async with tenant_session_context(tenant.organization_id) as session:
        result = await session.execute(text("select id,actor_id,agent_type,status,provider,model,confidence,escalation_required,result_summary,error_class,started_at,completed_at,created_at,updated_at from agent_executions order by created_at desc,id desc limit :limit offset :offset"), {'limit': limit, 'offset': offset})
        return [dict(r._mapping) for r in result]

@router.post('', status_code=202)
async def execute(payload: ExecutionRequest, http_request: Request, tenant: TenantContext = Depends(require_permission('agents:execute'))):
    try:
        agent = registry.get(payload.agent_type)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail='agent not found') from exc
    request = AgentRequest(task=payload.task, input=payload.input, idempotency_key=payload.idempotency_key, metadata={'data_classes': ','.join(payload.data_classes)})
    prompt_injection_detected = detect_prompt_injection(request)
    phi_boundary_violation = detect_phi_boundary_violation(request)
    effective_data_classes = tuple(sorted(set(payload.data_classes) | set(classify_input_data_classes(request))))
    async with tenant_session_context(tenant.organization_id) as session:
        clinic_id = await session.scalar(text("select id from clinics where clerk_org_id=:org"), {'org': tenant.organization_id})
        if not clinic_id:
            raise HTTPException(status_code=403, detail='organization clinic is not provisioned')
        repo = ExecutionRepository(session)
        existing = await repo.get_by_key(payload.agent_type, payload.idempotency_key)
        if existing:
            if existing['status'] in {'completed', 'failed', 'escalated', 'cancelled'}:
                return existing
            raise HTTPException(status_code=409, detail='execution already in progress')
        governance = AIGovernanceService(session, tenant.organization_id)
        initial = await governance.resolve_execution_policy(payload.agent_type, None, None, data_classes=effective_data_classes, tools=payload.tools, prompt_injection_detected=prompt_injection_detected, phi_boundary_violation=phi_boundary_violation)
        if initial.decision == 'deny':
            raise HTTPException(status_code=403, detail=initial.reason)
        execution = await repo.create(payload.agent_type, tenant.user_id, payload.idempotency_key, payload.task)
        await repo.mark_running(execution['id'])
        request_id = getattr(http_request.state, 'request_id', None)
        await append_event(session, organization_id=tenant.organization_id, actor=tenant.user_id, action='ai.execution.created', resource_type='agent_execution', resource_id=execution['id'], outcome='started', request_id=request_id, metadata={'capability_version': initial.capability_version, 'policy_version': initial.policy_version})
        context = AgentContext(tenant_id=tenant.organization_id, user_id=tenant.user_id, permissions=tenant.permissions, execution_id=execution['id'], request_id=request_id)
        try:
            response = await agent.execute(context, request)
            raw = response.output if isinstance(response.output, dict) else {}
            normalized = {'action': raw.get('action', ''), 'response': raw.get('response', ''), 'confidence': response.confidence if response.confidence is not None else 0, 'escalate': response.escalation_required}
            valid, failure = validate_output(normalized)
            action = normalized['action']
            provider = response.provider
            decision = await governance.resolve_execution_policy(payload.agent_type, action, provider, response.confidence, data_classes=effective_data_classes, tools=payload.tools, prompt_injection_detected=prompt_injection_detected, phi_boundary_violation=phi_boundary_violation)
            if decision.decision == 'deny':
                response = response.__class__('escalated', {'reason': decision.reason}, response.confidence, True, response.execution_id, provider, response.model)
            elif decision.decision == 'approval_required':
                approval_id = str(uuid.uuid4())
                await session.execute(text("insert into ai_approvals(id,clinic_id,execution_id,proposed_action,evidence,risk_tier,policy_version,decision,actor_id,expires_at) values(:id,:clinic,:execution,cast(:action as jsonb),'[]',:risk,:policy,'pending',:actor,now()+interval '30 minutes')"), {'id': approval_id, 'clinic': clinic_id, 'execution': execution['id'], 'action': json.dumps({'action': action}), 'risk': int(decision.risk_tier), 'policy': decision.policy_version or 'unknown', 'actor': tenant.user_id})
                response = response.__class__('escalated', {'reason': 'Human approval required', 'approval_id': approval_id}, response.confidence, True, response.execution_id, provider, response.model)
            elif decision.decision == 'escalate':
                response = response.__class__('escalated', {'reason': decision.reason}, response.confidence, True, response.execution_id, provider, response.model)
            status = response.status if response.status in {'completed', 'failed', 'escalated'} else 'failed'
            failure_category = failure or decision.failure_category
            await repo.complete(execution['id'], status, response.provider, response.model, response.confidence, response.escalation_required, str(response.output.get('response', '')) if isinstance(response.output, dict) else None, failure_category)
            await session.execute(text("insert into ai_policy_decisions(id,clinic_id,execution_id,policy_version_id,risk_tier,decision,reason) values(:id,:clinic,:execution,:policy,:risk,:decision,:reason)"), {'id': str(uuid.uuid4()), 'clinic': clinic_id, 'execution': execution['id'], 'policy': decision.policy_version_id, 'risk': int(decision.risk_tier), 'decision': decision.decision, 'reason': decision.reason})
            await session.execute(text("insert into ai_execution_telemetry(clinic_id,execution_id,capability_id,capability_version,request_id,provider,model,prompt_version,validation_result,confidence,escalation,approval_required,outcome,failure_category,safety_violation) values(:clinic,:execution,:capability,:version,:request,:provider,:model,:prompt,:validation,:confidence,:escalation,:approval,:outcome,:failure,:safety)"), {'clinic': clinic_id, 'execution': execution['id'], 'capability': decision.capability_id, 'version': decision.capability_version or 'unknown', 'request': request_id, 'provider': response.provider, 'model': response.model, 'prompt': decision.prompt_version or 'unknown', 'validation': 'valid' if valid else 'invalid', 'confidence': response.confidence, 'escalation': response.escalation_required, 'approval': decision.approval_required, 'outcome': status, 'failure': failure_category, 'safety': bool(prompt_injection_detected or phi_boundary_violation)})
            await append_event(session, organization_id=tenant.organization_id, actor=tenant.user_id, action=f'ai.execution.{status}', resource_type='agent_execution', resource_id=execution['id'], outcome=status, request_id=request_id, metadata={'capability_version': decision.capability_version, 'policy_version': decision.policy_version, 'policy_version_id': decision.policy_version_id, 'policy_decision': decision.decision, 'risk_tier': int(decision.risk_tier), 'failure_category': failure_category, 'prompt_injection_detected': prompt_injection_detected, 'phi_boundary_violation': phi_boundary_violation, 'effective_data_classes': list(effective_data_classes)})
            return {**response.__dict__}
        except HTTPException:
            raise
        except Exception as exc:
            await repo.complete(execution['id'], 'failed', None, None, None, True, None, type(exc).__name__)
            await session.execute(text("insert into ai_failure_events(clinic_id,execution_id,category,severity,detail) values(:clinic,:execution,'UNKNOWN','high','AI execution failed')"), {'clinic': clinic_id, 'execution': execution['id']})
            await append_event(session, organization_id=tenant.organization_id, actor=tenant.user_id, action='ai.execution.failed', resource_type='agent_execution', resource_id=execution['id'], outcome='failed', request_id=request_id, metadata={'error_class': type(exc).__name__})
            raise HTTPException(status_code=500, detail='AI execution failed') from exc
