from typing import Any
from clerk_backend_api import AuthenticateRequestOptions,authenticate_request
from fastapi import Depends,HTTPException,Request
from app.core.config import settings
from app.security.tenant import TenantContext
_BASE={'patients:read','patients:write','appointments:read','appointments:write','tasks:read','tasks:write','agents:read','agents:execute','executions:read','analytics:read','audit:read','compliance:read','compliance:manage','workflow:read','workflow:create','workflow:activate','workflow:execute','workflow:cancel','workflow:approve','approvals:read','approvals:approve','communications:read','communications:write','communications:send','billing:read','billing:write','insurance:read','insurance:write','eligibility:read','eligibility:write','authorization:read','authorization:write','claims:read','claims:write','claims:submit','referrals:read','referrals:write','records:read','integrations:read','integrations:manage','integrations:test','ai:governance:read','ai:governance:manage'}
_EXPORT={'analytics:export'}
ROLE_PERMISSIONS={
 'org:owner':frozenset(_BASE|_EXPORT),
 'org:admin':frozenset(_BASE|_EXPORT),
 'org:manager':frozenset((_BASE-{'compliance:manage','workflow:approve','approvals:approve','claims:submit','integrations:manage','ai:governance:manage'})|_EXPORT),
 'org:staff':frozenset(_BASE-{'compliance:manage','workflow:create','workflow:activate','workflow:cancel','workflow:approve','approvals:approve','claims:submit','integrations:manage','integrations:test','ai:governance:manage'}),
 'org:viewer':frozenset({'patients:read','appointments:read','tasks:read','agents:read','executions:read','analytics:read','workflow:read','approvals:read','communications:read','billing:read','insurance:read','eligibility:read','authorization:read','claims:read','referrals:read','records:read','integrations:read','ai:governance:read'}),
}
def _payload(state:Any)->dict[str,Any]: return state.get('payload',{}) if isinstance(state,dict) else (state.payload or {})
def verify_request(request:Request)->Any:
    if settings.app_env in {'test','development'} and request.headers.get('x-test-auth')=='1': return {'payload':{'sub':'test_user','org_id':'test_org','org_role':'org:admin'}}
    if not settings.clerk_secret_key or not settings.clerk_publishable_key: raise HTTPException(status_code=503,detail='authentication is not configured')
    if not settings.authorized_parties: raise HTTPException(status_code=503,detail='authorized parties are not configured')
    try: state=authenticate_request(request,AuthenticateRequestOptions(secret_key=settings.clerk_secret_key,publishable_key=settings.clerk_publishable_key,jwt_key=settings.clerk_jwt_key or None,authorized_parties=settings.authorized_parties,accepts_token=['session_token']))
    except Exception as exc: raise HTTPException(status_code=401,detail='unauthorized') from exc
    if not getattr(state,'is_authenticated',False): raise HTTPException(status_code=401,detail='unauthorized',headers={'WWW-Authenticate':'Bearer'})
    return state
async def get_auth_state(request:Request)->Any:return verify_request(request)
async def current_tenant(state:Any=Depends(get_auth_state))->TenantContext:
    payload=_payload(state); user_id=payload.get('sub'); organization_id=payload.get('org_id') or payload.get('organization_id')
    if not user_id or not organization_id: raise HTTPException(status_code=403,detail='organization context required')
    role=payload.get('org_role'); claims=payload.get('org_permissions'); permissions=frozenset(claims) if claims is not None else ROLE_PERMISSIONS.get(role,frozenset())
    return TenantContext(organization_id=organization_id,user_id=user_id,permissions=permissions,role=role)
