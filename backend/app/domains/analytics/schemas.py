from datetime import datetime
from pydantic import BaseModel


class AnalyticsWindow(BaseModel):
    start: datetime
    end: datetime


class MetricValue(BaseModel):
    key: str
    label: str
    value: int | float | None
    unit: str = "count"
    definition: str
    source_tables: list[str]


class AnalyticsSummary(BaseModel):
    window: AnalyticsWindow
    metrics: list[MetricValue]
    freshness: datetime


class DailyMetric(BaseModel):
    day: str
    calls: int
    appointments_booked: int
    appointments_completed: int
    no_shows: int
    tasks_completed: int
    escalated_tasks: int
    ai_executions: int
    ai_escalations: int
    workflows_completed: int
    workflows_failed: int
    communications_sent: int
    communications_failed: int


class FinancialSummary(BaseModel):
    window: AnalyticsWindow
    charges_amount: float
    patient_responsibility_amount: float
    payer_responsibility_amount: float
    payments_amount: float
    claims_billed_amount: float
    claims_paid_amount: float
    denied_claim_count: int
    denial_amount: float
    open_ar_amount: float
    definitions: dict[str, str]
    source_tables: list[str]


class InsuranceSummary(BaseModel):
    window: AnalyticsWindow
    eligibility_requests: int
    eligibility_verified: int
    eligibility_failed: int
    authorizations_submitted: int
    authorizations_approved: int
    authorizations_denied: int
    referrals_sent: int
    referrals_completed: int
    definitions: dict[str, str]
    source_tables: list[str]


class ComplianceSummary(BaseModel):
    window: AnalyticsWindow
    audit_events: int
    privileged_events: int
    ai_events: int
    integration_events: int
    failed_events: int
    definitions: dict[str, str]
    source_tables: list[str]
