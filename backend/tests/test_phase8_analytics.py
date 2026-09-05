from datetime import datetime, timezone

import pytest

from app.api.v1.analytics import _window
from app.domains.analytics.metrics import METRIC_BY_KEY
from app.domains.analytics.service import AnalyticsService


class FakeRepository:
    async def operational_summary(self, start, end):
        return {key: 1 for key in METRIC_BY_KEY} | {"total_patients": 3}

    async def daily(self, start, end):
        return [{"day": "2026-09-05", "calls": 1, "appointments_booked": 1, "appointments_completed": 1, "no_shows": 0, "tasks_completed": 1, "escalated_tasks": 0, "ai_executions": 1, "ai_escalations": 0, "workflows_completed": 1, "workflows_failed": 0, "communications_sent": 1, "communications_failed": 0}]

    async def financial_summary(self, start, end):
        return {"charges_amount": 100, "patient_responsibility_amount": 20, "payer_responsibility_amount": 80, "payments_amount": 50, "claims_billed_amount": 100, "claims_paid_amount": 50, "denied_claim_count": 1, "denial_amount": 20, "open_ar_amount": 70}

    async def insurance_summary(self, start, end):
        return {"eligibility_requests": 4, "eligibility_verified": 3, "eligibility_failed": 1, "authorizations_submitted": 2, "authorizations_approved": 1, "authorizations_denied": 0, "referrals_sent": 2, "referrals_completed": 1}

    async def compliance_summary(self, start, end):
        return {"audit_events": 5, "privileged_events": 1, "ai_events": 2, "integration_events": 1, "failed_events": 1}


@pytest.mark.asyncio
async def test_summary_uses_canonical_metric_definitions():
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    end = datetime(2026, 9, 5, tzinfo=timezone.utc)
    result = await AnalyticsService(FakeRepository()).summary(start, end)
    assert {metric["key"] for metric in result["metrics"]} == set(METRIC_BY_KEY)
    assert all(metric["definition"] for metric in result["metrics"])
    assert all(metric["source_tables"] for metric in result["metrics"])


def test_reporting_window_is_bounded_and_ordered():
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    end = datetime(2026, 9, 1, tzinfo=timezone.utc)
    assert _window(start, end) == (start, end)

    with pytest.raises(Exception):
        _window(end, start)

    with pytest.raises(Exception):
        _window(datetime(2025, 1, 1, tzinfo=timezone.utc), end)
