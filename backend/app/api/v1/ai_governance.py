from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.ai.governance.service import AIGovernanceService

router=APIRouter(prefix='/ai-governance',tags=['ai-governance'])
class ControlUpdate(BaseModel):
    ai_enabled:bool|None=None; force_human_approval:bool|None=None; force_deterministic_fallback:bool|None=None; disabled_capabilities:list[str]|None=None; disabled_providers:list[str]|None=None; tool_access_enabled:bool|None=None

def _page(limit:int,offset:int):
    if limit<1 or limit>100 or offset<0: raise HTTPException(status_code=400,detail='invalid pagination')
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
        result=await AIGovernanceService(s,tenant.organization_id).set_controls(payload.model_dump(exclude_none=True),tenant.user_id)
        from app.security.audit import append_event
        await append_event(s,organization_id=tenant.organization_id,actor=tenant.user_id,action='ai.governance.controls.changed',resource_type='ai_control_state',resource_id=tenant.organization_id,outcome='updated',request_id=getattr(request.state,'request_id',None),metadata={'fields':list(payload.model_dump(exclude_none=True))})
        return result
