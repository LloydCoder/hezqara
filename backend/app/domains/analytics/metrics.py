from dataclasses import dataclass


@dataclass(frozen=True)
class MetricDefinition:
    key: str
    label: str
    category: str
    definition: str
    formula: str
    unit: str
    source_tables: tuple[str, ...]
    time_field: str
    denominator: str | None
    null_behavior: str
    permission: str
    pii: bool = False
    drilldown: str | None = None


METRICS = (
    MetricDefinition("calls", "Calls", "operations", "Calls created inside the reporting window.", "count(calls)", "count", ("calls",), "calls.created_at", None, "zero when no rows match", "analytics:read", False, "calls"),
    MetricDefinition("appointments_booked", "Appointments booked", "operations", "Appointments created inside the window and not cancelled.", "count(appointments where status != cancelled)", "count", ("appointments",), "appointments.created_at", None, "zero when no rows match", "analytics:read", False, "appointments"),
    MetricDefinition("appointments_completed", "Appointments completed", "operations", "Appointments with completed status whose scheduled time falls inside the window.", "count(appointments where scheduled time is in window and status = completed)", "count", ("appointments",), "appointments.appointment_datetime", None, "zero when no rows match", "analytics:read", False, "appointments"),
    MetricDefinition("no_shows", "No-shows", "operations", "Appointments with no_show status whose scheduled time falls inside the window.", "count(appointments where scheduled time is in window and status = no_show)", "count", ("appointments",), "appointments.appointment_datetime", None, "zero when no rows match", "analytics:read", False, "appointments"),
    MetricDefinition("tasks_completed", "Tasks completed", "operations", "Tasks with completed status and an update timestamp inside the window.", "count(tasks where updated_at is in window and status = completed)", "count", ("tasks",), "tasks.updated_at", None, "zero when no rows match", "analytics:read", False, "tasks"),
    MetricDefinition("escalated_tasks", "Escalated tasks", "operations", "Tasks with escalated status and an update timestamp inside the window.", "count(tasks where updated_at is in window and status = escalated)", "count", ("tasks",), "tasks.updated_at", None, "zero when no rows match", "analytics:read", False, "tasks"),
    MetricDefinition("ai_executions", "AI executions", "AI workforce", "Agent executions created inside the reporting window.", "count(agent_executions)", "count", ("agent_executions",), "agent_executions.created_at", None, "zero when no rows match", "analytics:read", False, "executions"),
    MetricDefinition("ai_escalations", "AI escalations", "AI workforce", "Agent executions requiring escalation created inside the reporting window.", "count(agent_executions where escalation_required)", "count", ("agent_executions",), "agent_executions.created_at", "ai_executions", "zero when no rows match", "analytics:read", False, "executions"),
    MetricDefinition("workflows_completed", "Workflows completed", "workflow", "Workflow runs completed inside the reporting window.", "count(workflow_runs where completed_at is in window and status = completed)", "count", ("workflow_runs",), "workflow_runs.completed_at", None, "zero when no rows match", "analytics:read", False, "workflow_runs"),
    MetricDefinition("workflows_failed", "Workflows failed", "workflow", "Workflow runs failed inside the reporting window.", "count(workflow_runs where updated_at is in window and status = failed)", "count", ("workflow_runs",), "workflow_runs.updated_at", None, "zero when no rows match", "analytics:read", False, "workflow_runs"),
    MetricDefinition("communications_sent", "Communications sent", "communications", "Outbound communications sent or delivered inside the reporting window.", "count(communications where status in sent, delivered)", "count", ("communications",), "communications.created_at", None, "zero when no rows match", "analytics:read", False, "communications"),
    MetricDefinition("communications_failed", "Communications failed", "communications", "Communications with failed status inside the reporting window.", "count(communications where status = failed)", "count", ("communications",), "communications.created_at", None, "zero when no rows match", "analytics:read", False, "communications"),
    MetricDefinition("charges_amount", "Charges", "revenue_cycle", "Non-voided billing charges created in the reporting window.", "sum(billing_charges.amount where status != voided)", "currency", ("billing_charges",), "billing_charges.created_at", None, "zero when no rows match", "analytics:read", False, "billing_charges"),
    MetricDefinition("payments_amount", "Payments collected", "revenue_cycle", "Paid billing payments created in the reporting window.", "sum(billing_payments.amount where status = paid)", "currency", ("billing_payments",), "billing_payments.created_at", None, "zero when no rows match", "analytics:read", False, "billing_payments"),
    MetricDefinition("claims_billed_amount", "Claims billed", "revenue_cycle", "Billed amount on non-closed claims created in the reporting window.", "sum(claims.billed_amount where status != closed)", "currency", ("claims",), "claims.created_at", None, "zero when no rows match", "analytics:read", False, "claims"),
    MetricDefinition("denial_amount", "Denials", "revenue_cycle", "Denial amounts recorded in the reporting window.", "sum(denials.amount)", "currency", ("denials",), "denials.created_at", None, "zero when no rows match", "analytics:read", False, "denials"),
    MetricDefinition("eligibility_requests", "Eligibility requests", "insurance", "Eligibility requests initiated in the reporting window.", "count(eligibility_requests)", "count", ("eligibility_requests",), "eligibility_requests.requested_at", None, "zero when no rows match", "analytics:read", False, "eligibility_requests"),
    MetricDefinition("eligibility_failed", "Eligibility failures", "insurance", "Eligibility responses classified as failed, unavailable, provider error, ineligible, or verification failed.", "count(eligibility_requests where response status is a failure class)", "count", ("eligibility_requests",), "eligibility_requests.responded_at", "eligibility_requests with responses", "zero when no rows match", "analytics:read", False, "eligibility_requests"),
    MetricDefinition("authorizations_submitted", "Authorizations submitted", "insurance", "Authorizations with a submission timestamp in the reporting window.", "count(authorizations)", "count", ("authorizations",), "authorizations.submitted_at", None, "zero when no rows match", "analytics:read", False, "authorizations"),
    MetricDefinition("authorizations_denied", "Authorizations denied", "insurance", "Authorizations receiving denied status in the reporting window.", "count(authorizations where status = denied and response_at is in window)", "count", ("authorizations",), "authorizations.response_at", None, "zero when no rows match", "analytics:read", False, "authorizations"),
    MetricDefinition("referrals_completed", "Referrals completed", "insurance", "Referrals updated to completed in the reporting window.", "count(referrals_v2 where updated_at in window and status = completed)", "count", ("referrals_v2",), "referrals_v2.updated_at", None, "zero when no rows match", "analytics:read", False, "referrals_v2"),
    MetricDefinition("audit_events", "Audit events", "compliance", "Tenant-scoped audit events created in the reporting window.", "count(audit_log)", "count", ("audit_log",), "audit_log.created_at", None, "zero when no rows match", "compliance:read", False, "audit_log"),
    MetricDefinition("failed_events", "Failed audit events", "compliance", "Audit events explicitly classified as failed, error, denied, or rejected.", "count(audit_log where outcome in failed, error, denied, rejected)", "count", ("audit_log",), "audit_log.created_at", "audit_events", "zero when no rows match", "compliance:read", False, "audit_log"),
)

METRIC_BY_KEY = {metric.key: metric for metric in METRICS}
