from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext
from app.platform.enterprise import readiness, security_posture
from app.platform.scale import current_usage, get_limits, record_usage
from app.platform.commercial import PLAN_CATALOG, change_plan, create_checkout_session, get_subscription
from app.platform.growth import complete_onboarding_step, create_lead, onboarding_status

router = APIRouter(prefix="/platform", tags=["platform"])

class UsageRequest(BaseModel):
    metric: str = Field(min_length=1, max_length=80)
    amount: int = Field(default=1, ge=1, le=1_000_000)

class PlanRequest(BaseModel):
    plan_code: str = Field(min_length=1, max_length=40)

class CheckoutRequest(BaseModel):
    plan_code: str = Field(min_length=1, max_length=40)
    idempotency_key: str = Field(min_length=16, max_length=255)

class OnboardingRequest(BaseModel):
    step: str = Field(min_length=1, max_length=80)

class LeadRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    clinic_name: str | None = Field(default=None, max_length=200)
    source: str = Field(default="direct", min_length=1, max_length=80)
    campaign: str | None = Field(default=None, max_length=120)

@router.get("/readiness")
async def platform_readiness(tenant: TenantContext = Depends(require_permission("platform:read"))):
    async with tenant_session_context(tenant.organization_id) as session:
        result = await readiness(session)
        return {"status": result.status, "checks": result.checks}

@router.get("/security-posture")
async def platform_security(tenant: TenantContext = Depends(require_permission("platform:read"))):
    async with tenant_session_context(tenant.organization_id) as session:
        return await security_posture(session, tenant.organization_id)

@router.get("/limits")
async def limits(tenant: TenantContext = Depends(require_permission("platform:read"))):
    async with tenant_session_context(tenant.organization_id) as session:
        return await get_limits(session, tenant.organization_id)

@router.get("/usage")
async def usage(tenant: TenantContext = Depends(require_permission("analytics:read"))):
    async with tenant_session_context(tenant.organization_id) as session:
        return await current_usage(session, tenant.organization_id)

@router.post("/usage", status_code=201)
async def add_usage(payload: UsageRequest, tenant: TenantContext = Depends(require_permission("analytics:write"))):
    async with tenant_session_context(tenant.organization_id) as session:
        return await record_usage(session, tenant.organization_id, payload.metric, payload.amount)

@router.get("/plans")
async def plans():
    return {"plans": [{"code": code, **{k: str(v) if hasattr(v, "as_tuple") else v for k, v in plan.items()}} for code, plan in PLAN_CATALOG.items()]}

@router.get("/subscription")
async def subscription(tenant: TenantContext = Depends(require_permission("billing:read"))):
    async with tenant_session_context(tenant.organization_id) as session:
        return await get_subscription(session, tenant.organization_id)

@router.post("/subscription/checkout")
async def subscription_checkout(payload: CheckoutRequest, tenant: TenantContext = Depends(require_permission("billing:write"))):
    try:
        async with tenant_session_context(tenant.organization_id) as session:
            return await create_checkout_session(session, tenant.organization_id, payload.plan_code, payload.idempotency_key)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="payment provider request failed") from exc

@router.post("/subscription/plan")
async def plan(payload: PlanRequest, tenant: TenantContext = Depends(require_permission("billing:write"))):
    try:
        async with tenant_session_context(tenant.organization_id) as session:
            return await change_plan(session, tenant.organization_id, payload.plan_code, tenant.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.get("/onboarding")
async def onboarding(tenant: TenantContext = Depends(require_permission("platform:read"))):
    async with tenant_session_context(tenant.organization_id) as session:
        return await onboarding_status(session, tenant.organization_id)

@router.post("/onboarding/complete")
async def onboarding_complete(payload: OnboardingRequest, tenant: TenantContext = Depends(require_permission("platform:write"))):
    try:
        async with tenant_session_context(tenant.organization_id) as session:
            return await complete_onboarding_step(session, tenant.organization_id, payload.step, tenant.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.post("/leads", status_code=201)
async def lead(payload: LeadRequest, tenant: TenantContext = Depends(require_permission("platform:write"))):
    async with tenant_session_context(tenant.organization_id) as session:
        return await create_lead(session, tenant.organization_id, payload.email, payload.clinic_name, payload.source, payload.campaign)
