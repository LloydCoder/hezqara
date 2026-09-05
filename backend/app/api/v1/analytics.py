import csv
import io
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.domains.analytics.metrics import METRIC_BY_KEY
from app.domains.analytics.repository import AnalyticsRepository
from app.domains.analytics.schemas import AnalyticsSummary, ComplianceEvidenceResponse, ComplianceSummary, DailyMetric, ExecutiveIntelligence, FinancialSummary, InsuranceSummary, MetricCatalogResponse, MetricTraceResponse
from app.domains.analytics.service import AnalyticsService
from app.infrastructure.database import tenant_session_context
from app.security.audit import append_event
from app.security.authorization import require_permission
from app.security.tenant import TenantContext

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _window(start: datetime | None, end: datetime | None) -> tuple[datetime, datetime]:
    resolved_end = (end or datetime.now(timezone.utc)).astimezone(timezone.utc)
    resolved_start = (start or resolved_end - timedelta(days=30)).astimezone(timezone.utc)
    if resolved_start >= resolved_end:
        raise HTTPException(status_code=422, detail="start must be before end")
    if resolved_end - resolved_start > timedelta(days=366):
        raise HTTPException(status_code=422, detail="reporting window cannot exceed 366 days")
    return resolved_start, resolved_end


@router.get("/summary", response_model=AnalyticsSummary)
async def summary(start: datetime | None = Query(default=None), end: datetime | None = Query(default=None), tenant: TenantContext = Depends(require_permission("analytics:read"))):
    start, end = _window(start, end)
    async with tenant_session_context(tenant.organization_id) as session:
        return await AnalyticsService(AnalyticsRepository(session)).summary(start, end)


@router.get("/catalog", response_model=MetricCatalogResponse)
async def catalog(tenant: TenantContext = Depends(require_permission("analytics:read"))):
    async with tenant_session_context(tenant.organization_id) as session:
        return await AnalyticsService(AnalyticsRepository(session)).catalog()


@router.get("/daily", response_model=list[DailyMetric])
async def daily(start: datetime | None = Query(default=None), end: datetime | None = Query(default=None), tenant: TenantContext = Depends(require_permission("analytics:read"))):
    start, end = _window(start, end)
    async with tenant_session_context(tenant.organization_id) as session:
        return await AnalyticsService(AnalyticsRepository(session)).daily(start, end)


@router.get("/financial", response_model=FinancialSummary)
async def financial(start: datetime | None = Query(default=None), end: datetime | None = Query(default=None), tenant: TenantContext = Depends(require_permission("analytics:read"))):
    start, end = _window(start, end)
    async with tenant_session_context(tenant.organization_id) as session:
        return await AnalyticsService(AnalyticsRepository(session)).financial(start, end)


@router.get("/insurance", response_model=InsuranceSummary)
async def insurance(start: datetime | None = Query(default=None), end: datetime | None = Query(default=None), tenant: TenantContext = Depends(require_permission("analytics:read"))):
    start, end = _window(start, end)
    async with tenant_session_context(tenant.organization_id) as session:
        return await AnalyticsService(AnalyticsRepository(session)).insurance(start, end)


@router.get("/compliance", response_model=ComplianceSummary)
async def compliance(start: datetime | None = Query(default=None), end: datetime | None = Query(default=None), tenant: TenantContext = Depends(require_permission("compliance:read"))):
    start, end = _window(start, end)
    async with tenant_session_context(tenant.organization_id) as session:
        return await AnalyticsService(AnalyticsRepository(session)).compliance(start, end)


@router.get("/compliance/evidence", response_model=ComplianceEvidenceResponse)
async def evidence(
    start: datetime | None = Query(default=None), end: datetime | None = Query(default=None),
    action: str | None = Query(default=None, max_length=120), outcome: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0),
    tenant: TenantContext = Depends(require_permission("compliance:read")),
):
    start, end = _window(start, end)
    async with tenant_session_context(tenant.organization_id) as session:
        return await AnalyticsService(AnalyticsRepository(session)).evidence(start, end, limit, offset, action, outcome)


@router.get("/metric/{key}/trace", response_model=MetricTraceResponse)
async def trace(key: str, start: datetime | None = Query(default=None), end: datetime | None = Query(default=None), tenant: TenantContext = Depends(require_permission("analytics:read"))):
    definition = METRIC_BY_KEY.get(key)
    if not definition:
        raise HTTPException(status_code=404, detail="unknown metric")
    if definition.permission == "compliance:read":
        tenant.require("compliance:read")
    start, end = _window(start, end)
    async with tenant_session_context(tenant.organization_id) as session:
        return await AnalyticsService(AnalyticsRepository(session)).trace(key, start, end)


@router.get("/executive", response_model=ExecutiveIntelligence)
async def executive(start: datetime | None = Query(default=None), end: datetime | None = Query(default=None), tenant: TenantContext = Depends(require_permission("analytics:read"))):
    start, end = _window(start, end)
    async with tenant_session_context(tenant.organization_id) as session:
        return await AnalyticsService(AnalyticsRepository(session)).executive(start, end)


@router.get("/export")
async def export_csv(
    request: Request, start: datetime | None = Query(default=None), end: datetime | None = Query(default=None),
    tenant: TenantContext = Depends(require_permission("analytics:export")),
):
    start, end = _window(start, end)
    async with tenant_session_context(tenant.organization_id) as session:
        service = AnalyticsService(AnalyticsRepository(session))
        rows = await service.daily(start, end)
        allowed = [
            "day", "calls", "appointments_booked", "appointments_completed", "no_shows", "tasks_completed",
            "escalated_tasks", "ai_executions", "ai_escalations", "workflows_completed", "workflows_failed",
            "communications_sent", "communications_failed", "charges_amount", "payments_amount", "denial_amount",
            "eligibility_requests", "eligibility_failed", "authorizations_submitted", "authorizations_denied", "referrals_completed",
        ]
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=allowed, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        await append_event(session, organization_id=tenant.organization_id, actor=tenant.user_id, action="analytics.exported", resource_type="analytics_export", resource_id=None, outcome="success", request_id=getattr(request.state, "request_id", None), metadata={"format":"csv", "row_count":len(rows), "start":start.isoformat(), "end":end.isoformat(), "fields":allowed})
        content = buffer.getvalue()
    filename = f"hezqara-analytics-{start.date().isoformat()}-{end.date().isoformat()}.csv"
    return StreamingResponse(iter([content]), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control":"no-store"})
