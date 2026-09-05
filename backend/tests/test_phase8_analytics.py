from datetime import datetime, timezone
import pytest
from app.api.v1.analytics import _window
from app.domains.analytics.metrics import METRIC_BY_KEY
from app.domains.analytics.service import AnalyticsService

class FakeRepository:
    async def operational_summary(self,start,end): return {key:1 for key in METRIC_BY_KEY}
    async def daily(self,start,end): return [{"day":"2026-09-05","calls":1,"appointments_booked":1,"appointments_completed":1,"no_shows":0,"tasks_completed":1,"escalated_tasks":0,"ai_executions":10,"ai_escalations":3,"workflows_completed":1,"workflows_failed":0,"communications_sent":1,"communications_failed":0,"charges_amount":100,"payments_amount":50,"denial_amount":20,"eligibility_requests":4,"eligibility_failed":1,"authorizations_submitted":2,"authorizations_denied":0,"referrals_completed":1}]
    async def financial_summary(self,start,end): return {"charges_amount":100,"patient_responsibility_amount":20,"payer_responsibility_amount":80,"payments_amount":50,"claims_billed_amount":100,"claims_paid_amount":50,"claim_count":10,"denied_claim_count":2,"denial_amount":20,"open_ar_amount":70}
    async def insurance_summary(self,start,end): return {"eligibility_requests":4,"eligibility_verified":3,"eligibility_failed":1,"authorizations_submitted":2,"authorizations_approved":1,"authorizations_denied":0,"referrals_sent":2,"referrals_completed":1}
    async def compliance_summary(self,start,end): return {"audit_events":100,"privileged_events":1,"ai_events":2,"integration_events":1,"failed_events":3}
    async def metric_trace(self,key,start,end): return [{"source_table":"calls","time_field":"calls.created_at","day":"2026-09-05","status":None,"count":4,"amount":None}]
    async def compliance_evidence(self,start,end,limit,offset,action,outcome): return [],0

@pytest.mark.asyncio
async def test_summary_uses_canonical_metric_definitions():
    start=datetime(2026,9,1,tzinfo=timezone.utc);end=datetime(2026,9,5,tzinfo=timezone.utc);result=await AnalyticsService(FakeRepository()).summary(start,end)
    assert {metric["key"] for metric in result["metrics"]}==set(METRIC_BY_KEY)
    assert all(metric["definition"] and metric["formula"] and metric["time_field"] for metric in result["metrics"])
    assert all(metric["source_tables"] for metric in result["metrics"])

@pytest.mark.asyncio
async def test_financial_denial_rate_uses_claim_count_not_amount():
    result=await AnalyticsService(FakeRepository()).financial(datetime(2026,9,1,tzinfo=timezone.utc),datetime(2026,9,5,tzinfo=timezone.utc))
    assert result["denial_rate"]==0.2
    assert result["collection_rate"]==0.5

@pytest.mark.asyncio
async def test_trace_and_executive_are_source_governed():
    start=datetime(2026,9,1,tzinfo=timezone.utc);end=datetime(2026,9,5,tzinfo=timezone.utc);service=AnalyticsService(FakeRepository())
    trace=await service.trace("calls",start,end);executive=await service.executive(start,end)
    assert trace["rows"][0]["source_table"]=="calls"
    assert any(r["key"]=="ai_escalation_rate" for r in executive["risks"])
    assert executive["financial"]["denial_rate"]==0.2

@pytest.mark.asyncio
async def test_catalog_contains_governance_metadata():
    result=await AnalyticsService(FakeRepository()).catalog()
    assert result["metrics"]
    assert all(m["permission"] and m["null_behavior"] and m["denominator"] is not None or m["denominator"] is None for m in result["metrics"])

def test_reporting_window_is_bounded_and_ordered():
    start=datetime(2026,8,1,tzinfo=timezone.utc);end=datetime(2026,9,1,tzinfo=timezone.utc);assert _window(start,end)==(start,end)
    with pytest.raises(Exception): _window(end,start)
    with pytest.raises(Exception): _window(datetime(2025,1,1,tzinfo=timezone.utc),end)
