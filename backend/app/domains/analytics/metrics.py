from dataclasses import dataclass


@dataclass(frozen=True)
class MetricDefinition:
    key: str
    label: str
    definition: str
    unit: str
    source_tables: tuple[str, ...]


METRICS = (
    MetricDefinition("calls", "Calls", "Calls created inside the selected reporting window.", "count", ("calls",)),
    MetricDefinition("appointments_booked", "Appointments booked", "Appointments created inside the window and not cancelled.", "count", ("appointments",)),
    MetricDefinition("appointments_completed", "Appointments completed", "Appointments with completed status whose scheduled time falls inside the window.", "count", ("appointments",)),
    MetricDefinition("no_shows", "No-shows", "Appointments with no_show status whose scheduled time falls inside the window.", "count", ("appointments",)),
    MetricDefinition("tasks_completed", "Tasks completed", "Tasks transitioned to completed with an update timestamp inside the window.", "count", ("tasks",)),
    MetricDefinition("escalated_tasks", "Escalated tasks", "Tasks with escalated status and an update timestamp inside the window.", "count", ("tasks",)),
    MetricDefinition("ai_executions", "AI executions", "Agent executions created inside the reporting window.", "count", ("agent_executions",)),
    MetricDefinition("ai_escalations", "AI escalations", "Agent executions requiring escalation created inside the reporting window.", "count", ("agent_executions",)),
    MetricDefinition("workflows_completed", "Workflows completed", "Workflow runs completed inside the reporting window.", "count", ("workflow_runs",)),
    MetricDefinition("workflows_failed", "Workflows failed", "Workflow runs failed inside the reporting window.", "count", ("workflow_runs",)),
    MetricDefinition("communications_sent", "Communications sent", "Outbound communications sent or delivered inside the reporting window.", "count", ("communications",)),
    MetricDefinition("communications_failed", "Communications failed", "Communications with failed status inside the reporting window.", "count", ("communications",)),
)

METRIC_BY_KEY = {metric.key: metric for metric in METRICS}
