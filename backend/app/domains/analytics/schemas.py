from datetime import datetime
from pydantic import BaseModel, Field


class AnalyticsWindow(BaseModel):
    start: datetime
    end: datetime


class MetricValue(BaseModel):
    key: str
    label: str
    category: str
    value: int | float | None
    unit: str = "count"
    definition: str
    formula: str
    source_tables: list[str]
    time_field: str
    denominator: str | None
    null_behavior: str
    permission: str
    pii: bool
    drilldown: str | None


class AnalyticsSummary(BaseModel):
    window: AnalyticsWindow
    metrics: list[MetricValue]
    freshness: datetime


class DailyMetric(BaseModel):
    day: str
    calls: int = 0
    appointments_booked: int = 0
    appointments_completed: int = 0
    no_shows: int = 0
    tasks_completed: int = 0
    escalated_tasks: int = 0
    ai_executions: int = 0
    ai_escalations: int = 0
    workflows_completed: int = 0
    workflows_failed: int = 0
    communications_sent: int = 0
    communications_failed: int = 0
    charges_amount: float = 0
    payments_amount: float = 0
    denial_amount: float = 0
    eligibility_requests: int = 0
    eligibility_failed: int = 0
    authorizations_submitted: int = 0
    authorizations_denied: int = 0
    referrals_completed: int = 0


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
    collection_rate: float | None = None
    denial_rate: float | None = None
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
    eligibility_success_rate: float | None = None
    authorization_approval_rate: float | None = None
    definitions: dict[str, str]
    source_tables: list[str]


class ComplianceSummary(BaseModel):
    window: AnalyticsWindow
    audit_events: int
    privileged_events: int
    ai_events: int
    integration_events: int
    failed_events: int
    failure_rate: float | None = None
    definitions: dict[str, str]
    source_tables: list[str]


class MetricCatalogResponse(BaseModel):
    metrics: list[MetricValue]
    generated_at: datetime


class TraceItem(BaseModel):
    source_table: str
    time_field: str
    day: str
    status: str | None = None
    count: int = 0
    amount: float | None = None


class MetricTraceResponse(BaseModel):
    metric: MetricValue
    window: AnalyticsWindow
    rows: list[TraceItem]
    total_rows: int


class ExecutiveRisk(BaseModel):
    key: str
    severity: str = Field(pattern="^(low|medium|high)$")
    title: str
    explanation: str
    source_metrics: list[str]


class ExecutiveIntelligence(BaseModel):
    window: AnalyticsWindow
    headline: str
    operational: AnalyticsSummary
    financial: FinancialSummary
    insurance: InsuranceSummary
    compliance: ComplianceSummary
    risks: list[ExecutiveRisk]
    freshness: datetime


class ComplianceEvidenceItem(BaseModel):
    id: str
    created_at: datetime
    action: str
    resource_type: str
    resource_id: str | None
    outcome: str
    actor_id: str | None
    agent_type: str | None
    request_id: str | None
    metadata: dict


class ComplianceEvidenceResponse(BaseModel):
    window: AnalyticsWindow
    events: list[ComplianceEvidenceItem]
    total: int
    limit: int
    offset: int


class AnalyticsExportResponse(BaseModel):
    format: str
    row_count: int
    window: AnalyticsWindow
    fields: list[str]
    generated_at: datetime
