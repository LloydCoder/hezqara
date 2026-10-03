from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy import text
import uuid
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.ai.governance.service import AIGovernanceService
from app.ai.governance.evaluation import evaluate_case
from app.security.audit import append_event
router=APIRouter(prefix='/ai-governance',tags=['ai-governance'])
class ControlUpdate(BaseModel):
    ai_enabled:bool|None=None;force_human_approval:bool|None=None;force_deterministic_fallback:bool|None=None;disabled_capabilities:list[str]|None=None;disabled_providers:list[str]|None=None;tool_access_enabled:bool|None=None
class SuiteCreate(BaseModel):
    capability_id:str=Field(min_length=1,max_length=100);version:str=Field(min_length=1,max_length=50);name:str=Field(min_length=1,max_length=200);description:str='';quality_threshold:float=Field(.8,ge=0,le=1);safety_threshold:float=Field(1,ge=0,le=1)
class CaseCreate(BaseModel):
    suite_id:int;case_key:str=Field(min_length=1,max_length=100);dataset_version:str=Field(min_length=1,max_length=50);category:str=Field(min_length=1,max_length=80);input:dict;expected:dict;constraints:dict={}
class ResultCreate(BaseModel):
    run_id:str;case_id:int;observed:dict;latency_ms:int|None=Field(None,ge=0);token_usage:int|None=Field(None,ge=0)
def _page(limit:int,offset:int):
    if limit<1 or limit>100 or offset<0:raise HTTPException(status_code=400,detail='invalid pagination')
    return limit,offset
@router.get('/summary')
async def summary(tenant:TenantContext=Depends(require_permission('ai:governance:read'))):
    async with tenant_session_context(tenant.organization_id) as s:return await AIGovernanceService(s,tenant.organization_id).governance_summary()
@router.get('/capabilities')
async def capabilities(limit:int=50,offset:int=0,tenant:TenantContext=Depends(require_permission('ai:governance:read'))):
    limit,offset=_page(limit,offset)
    async with tenant_session_context(tenant.organization_id) as s:return await AIGovernanceService(s,tenant.organization_id).capabilities(limit,offset)
@router.get('/capabilities/{capability_id}')
async def capability(capability_id:str,tenant:TenantContext=Depends(require_permission('ai:governance:read'))):
    async with tenant_session_context(tenant.organization_id) as s:
        row=await AIGovernanceService(s,tenant.organization_id).capability(capability_id)
        if not row:raise HTTPException(status_code=404,detail='capability not found')
        return row
@router.get('/telemetry')
async def telemetry(limit:int=50,offset:int=0,tenant:TenantContext=Depends(require_permission('ai:governance:read'))):
    limit,offset=_page(limit,offset)
    async with tenant_session_context(tenant.organization_id) as s:return await AIGovernanceService(s,tenant.organization_id).telemetry(limit,offset)
@router.get('/failures')
async def failures(limit:int=50,offset:int=0,tenant:TenantContext=Depends(require_permission('ai:governance:read'))):
    limit,offset=_page(limit,offset)
    async with tenant_session_context(tenant.organization_id) as s:return await AIGovernanceService(s,tenant.organization_id).failures(limit,offset)
@router.get('/approvals')
async def approvals(limit:int=50,offset:int=0,tenant:TenantContext=Depends(require_permission('ai:governance:read'))):
    limit,offset=_page(limit,offset)
    async with tenant_session_context(tenant.organization_id) as s:return await AIGovernanceService(s,tenant.organization_id).approvals(limit,offset)
@router.get('/controls')
async def controls(tenant:TenantContext=Depends(require_permission('ai:governance:read'))):
    async with tenant_session_context(tenant.organization_id) as s:return await AIGovernanceService(s,tenant.organization_id).controls()
@router.put('/controls')
async def update_controls(payload:ControlUpdate,request:Request,tenant:TenantContext=Depends(require_permission('ai:governance:manage'))):
    async with tenant_session_context(tenant.organization_id) as s:
        result=await AIGovernanceService(s,tenant.organization_id).set_controls(payload.model_dump(exclude_none=True),tenant.user_id);await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,action='ai.governance.controls.changed',resource_type='ai_control_state',resource_id=tenant.organization_id,outcome='updated',request_id=getattr(request.state,'request_id',None),metadata={'fields':list(payload.model_dump(exclude_none=True))});return result
@router.get('/evaluation/suites')
async def suites(limit:int=50,offset:int=0,tenant:TenantContext=Depends(require_permission('ai:governance:read'))):
    limit,offset=_page(limit,offset)
    async with tenant_session_context(tenant.organization_id) as s:
        r=await s.execute(text("select id,capability_id,version,name,status,quality_threshold,safety_threshold,created_at from ai_evaluation_suites where clinic_id=:tenant order by created_at desc limit :limit offset :offset"),{'tenant':tenant.organization_id,'limit':limit,'offset':offset});return [dict(x._mapping) for x in r]
@router.post('/evaluation/suites',status_code=201)
async def create_suite(payload:SuiteCreate,request:Request,tenant:TenantContext=Depends(require_permission('ai:governance:manage'))):
    async with tenant_session_context(tenant.organization_id) as s:
        exists=(await s.execute(text("select 1 from ai_capabilities where clinic_id=:tenant and id=:id"),{'tenant':tenant.organization_id,'id':payload.capability_id})).first()
        if not exists:raise HTTPException(status_code=404,detail='capability not found')
        r=await s.execute(text("insert into ai_evaluation_suites(clinic_id,capability_id,version,name,description,quality_threshold,safety_threshold) values(:tenant,:cap,:version,:name,:description,:quality,:safety) returning id,capability_id,version,name,status,quality_threshold,safety_threshold,created_at"),{'tenant':tenant.organization_id,'cap':payload.capability_id,'version':payload.version,'name':payload.name,'description':payload.description,'quality':payload.quality_threshold,'safety':payload.safety_threshold});row=dict(r.mappings().one());await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,action='ai.evaluation.suite.created',resource_type='ai_evaluation_suite',resource_id=str(row['id']),outcome='created',request_id=getattr(request.state,'request_id',None));return row
@router.get('/evaluation/cases')
async def cases(suite_id:int,limit:int=50,offset:int=0,tenant:TenantContext=Depends(require_permission('ai:governance:read'))):
    limit,offset=_page(limit,offset)
    async with tenant_session_context(tenant.organization_id) as s:
        r=await s.execute(text("select id,suite_id,case_key,dataset_version,category,input,expected,constraints,synthetic_only,created_at from ai_evaluation_cases where clinic_id=:tenant and suite_id=:suite order by id limit :limit offset :offset"),{'tenant':tenant.organization_id,'suite':suite_id,'limit':limit,'offset':offset});return [dict(x._mapping) for x in r]
@router.post('/evaluation/cases',status_code=201)
async def create_case(payload:CaseCreate,tenant:TenantContext=Depends(require_permission('ai:governance:manage'))):
    async with tenant_session_context(tenant.organization_id) as s:
        try:r=await s.execute(text("insert into ai_evaluation_cases(clinic_id,suite_id,case_key,dataset_version,category,input,expected,constraints,synthetic_only) values(:tenant,:suite,:key,:dataset,:category,cast(:input as jsonb),cast(:expected as jsonb),cast(:constraints as jsonb),true) returning id,case_key,dataset_version,category,synthetic_only"),{'tenant':tenant.organization_id,'suite':payload.suite_id,'key':payload.case_key,'dataset':payload.dataset_version,'category':payload.category,'input':__import__('json').dumps(payload.input),'expected':__import__('json').dumps(payload.expected),'constraints':__import__('json').dumps(payload.constraints)})
        except Exception as exc:raise HTTPException(status_code=400,detail='evaluation case could not be created') from exc
        return dict(r.mappings().one())
@router.post('/evaluation/runs',status_code=201)
async def create_run(suite_id:int,tenant:TenantContext=Depends(require_permission('ai:governance:manage'))):
    async with tenant_session_context(tenant.organization_id) as s:
        suite=(await s.execute(text("select * from ai_evaluation_suites where clinic_id=:tenant and id=:id"),{'tenant':tenant.organization_id,'id':suite_id})).mappings().first()
        if not suite:raise HTTPException(status_code=404,detail='evaluation suite not found')
        run_id=str(uuid.uuid4());await s.execute(text("insert into ai_evaluation_runs(id,clinic_id,suite_id,status,started_at) values(:id,:tenant,:suite,'running',now())"),{'id':run_id,'tenant':tenant.organization_id,'suite':suite_id});return {'id':run_id,'suite_id':suite_id,'status':'running','note':'Awaiting governed model observations; no benchmark is fabricated.'}
@router.post('/evaluation/results',status_code=201)
async def create_result(payload:ResultCreate,tenant:TenantContext=Depends(require_permission('ai:governance:manage'))):
    async with tenant_session_context(tenant.organization_id) as s:
        case=(await s.execute(text("select expected from ai_evaluation_cases where clinic_id=:tenant and id=:id"),{'tenant':tenant.organization_id,'id':payload.case_id})).mappings().first()
        if not case:raise HTTPException(status_code=404,detail='evaluation case not found')
        result=evaluate_case(payload.observed,case['expected']);await s.execute(text("insert into ai_evaluation_results(clinic_id,run_id,case_id,passed,safety_passed,score,latency_ms,token_usage,failure_category,observed,evidence) values(:tenant,:run,:case,:passed,:safety,:score,:latency,:tokens,:failure,cast(:observed as jsonb),cast(:evidence as jsonb))"),{'tenant':tenant.organization_id,'run':payload.run_id,'case':payload.case_id,'passed':result['passed'],'safety':result['safety_passed'],'score':result['score'],'latency':payload.latency_ms,'tokens':payload.token_usage,'failure':result['failure_category'],'observed':__import__('json').dumps(payload.observed),'evidence':__import__('json').dumps(payload.observed.get('evidence',[]))});return result

class ToolPolicyCreate(BaseModel):
    tool_key:str=Field(min_length=2,max_length=200);interface_type:str='mcp';risk_tier:int=Field(ge=0,le=5);tenant_scoped:bool=True;side_effect:bool=False;approval_required:bool=False;idempotent:bool=True;allowed_data_classes:list[str]=[];allowed_actions:list[str]=[]

@router.get('/tools')
async def tool_policies(tenant:TenantContext=Depends(require_permission('ai:governance:read'))):
    async with tenant_session_context(tenant.organization_id) as s:return await AIGovernanceService(s,tenant.organization_id).tool_policies()

@router.post('/tools',status_code=201)
async def create_tool_policy(payload:ToolPolicyCreate,request:Request,tenant:TenantContext=Depends(require_permission('ai:governance:manage'))):
    if payload.interface_type not in {'mcp','native','fhir','rest'}:raise HTTPException(422,detail='invalid tool interface')
    if payload.side_effect and payload.risk_tier>=3 and not payload.approval_required:raise HTTPException(422,detail='high-risk side effects require approval')
    async with tenant_session_context(tenant.organization_id) as s:
        clinic=await AIGovernanceService(s,tenant.organization_id)._clinic_id()
        r=await s.execute(text("insert into ai_tool_policies(clinic_id,tool_key,interface_type,risk_tier,tenant_scoped,side_effect,approval_required,idempotent,allowed_data_classes,allowed_actions) values(:clinic,:tool,:interface,:risk,:tenant_scoped,:side_effect,:approval,:idempotent,cast(:data as jsonb),cast(:actions as jsonb)) on conflict(clinic_id,tool_key) do update set interface_type=excluded.interface_type,risk_tier=excluded.risk_tier,tenant_scoped=excluded.tenant_scoped,side_effect=excluded.side_effect,approval_required=excluded.approval_required,idempotent=excluded.idempotent,allowed_data_classes=excluded.allowed_data_classes,allowed_actions=excluded.allowed_actions,updated_at=now() returning id,tool_key,interface_type,risk_tier,tenant_scoped,side_effect,approval_required,idempotent,allowed_data_classes,allowed_actions,status,version"),{'clinic':clinic,'tool':payload.tool_key,'interface':payload.interface_type,'risk':payload.risk_tier,'tenant_scoped':payload.tenant_scoped,'side_effect':payload.side_effect,'approval':payload.approval_required,'idempotent':payload.idempotent,'data':__import__('json').dumps(payload.allowed_data_classes),'actions':__import__('json').dumps(payload.allowed_actions)})
        return dict(r.mappings().one())

@router.post('/tools/authorize')
async def authorize_tool(tool_key:str,interface_type:str='mcp',action:str|None=None,data_classes:str='',tenant:TenantContext=Depends(require_permission('ai:governance:read'))):
    classes=[x for x in data_classes.split(',') if x]
    async with tenant_session_context(tenant.organization_id) as s:return await AIGovernanceService(s,tenant.organization_id).authorize_tool(tool_key,interface_type,classes,action)
