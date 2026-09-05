from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query

from app.domains.analytics.repository import AnalyticsRepository
from app.domains.analytics.schemas import AnalyticsSummary, ComplianceSummary, DailyMetric, FinancialSummary, InsuranceSummary
from app.domains.analytics.service import AnalyticsService
from app.infrastructure.database import tenant_session_context
from app.security.authorization import require_permission
from app.security.tenant import TenantContext

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _window(start: datetime | None, end: datetime | None) -> tuple[datetime, datetime]:
    resolved_end = (end or datetime.now(timezone.utc)).astimezone(timezone.utc)
    resolved_start = (start or resolved_end - timedelta(days=30)).astimezone(timezone.utc)
    if resolved_start >= resolved_end:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="start must be before end")
    if resolved_end - resolved_start > timedelta(days=366):
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="reporting window cannot exceed 366 days")
    return resolved_start, resolved_end


async def _service(tenant: TenantContext) -> AnalyticsService:
    raise RuntimeError("dependency placeholder")


@router.get("/summary", response_model=AnalyticsSummary)
async def summary(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    tenant: TenantContext = Depends(require_permission("analytics:read")),
):
    start, end = _window(start, end)
    async with tenant_session_context(tenant.organization_id) as session:
        return await AnalyticsService(AnalyticsRepository(session)).summary(start, end)


@router.get("/daily", response_model=list[DailyMetric])
async def daily(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    tenant: TenantContext = Depends(require_permission("analytics:read")),
):
    start, end = _window(start, end)
    async with tenant_session_context(tenant.organization_id) as session:
        return await AnalyticsService(AnalyticsRepository(session)).daily(start, end)


@router.get("/financial", response_model=FinancialSummary)
async def financial(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    tenant: TenantContext = Depends(require_permission("analytics:read")),
):
    start, end = _window(start, end)
    async with tenant_session_context(tenant.organization_id) as session:
        return await AnalyticsService(AnalyticsRepository(session)).financial(start, end)


@router.get("/insurance", response_model=InsuranceSummary)
async def insurance(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    tenant: TenantContext = Depends(require_permission("analytics:read")),
):
    start, end = _window(start, end)
    async with tenant_session_context(tenant.organization_id) as session:
        return await AnalyticsService(AnalyticsRepository(session)).insurance(start, end)


@router.get("/compliance", response_model=ComplianceSummary)
async def compliance(
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    tenant: TenantContext = Depends(require_permission("compliance:read")),
):
    start, end = _window(start, end)
    async with tenant_session_context(tenant.organization_id) as session:
        return await AnalyticsService(AnalyticsRepository(session)).compliance(start, end)
