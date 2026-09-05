from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def operational_summary(self, start: datetime, end: datetime) -> dict:
        result = await self.session.execute(text("""
            SELECT
              (SELECT count(*) FROM calls WHERE created_at >= :start AND created_at < :end) AS calls,
              (SELECT count(*) FROM appointments WHERE created_at >= :start AND created_at < :end AND status <> 'cancelled') AS appointments_booked,
              (SELECT count(*) FROM appointments WHERE appointment_datetime >= :start AND appointment_datetime < :end AND status = 'completed') AS appointments_completed,
              (SELECT count(*) FROM appointments WHERE appointment_datetime >= :start AND appointment_datetime < :end AND status = 'no_show') AS no_shows,
              (SELECT count(*) FROM tasks WHERE updated_at >= :start AND updated_at < :end AND status = 'completed') AS tasks_completed,
              (SELECT count(*) FROM tasks WHERE updated_at >= :start AND updated_at < :end AND status = 'escalated') AS escalated_tasks,
              (SELECT count(*) FROM agent_executions WHERE created_at >= :start AND created_at < :end) AS ai_executions,
              (SELECT count(*) FROM agent_executions WHERE created_at >= :start AND created_at < :end AND escalation_required) AS ai_escalations,
              (SELECT count(*) FROM workflow_runs WHERE completed_at >= :start AND completed_at < :end AND status = 'completed') AS workflows_completed,
              (SELECT count(*) FROM workflow_runs WHERE updated_at >= :start AND updated_at < :end AND status = 'failed') AS workflows_failed,
              (SELECT count(*) FROM communications WHERE created_at >= :start AND created_at < :end AND status IN ('sent','delivered')) AS communications_sent,
              (SELECT count(*) FROM communications WHERE created_at >= :start AND created_at < :end AND status = 'failed') AS communications_failed,
              (SELECT count(*) FROM patients) AS total_patients
        """), {"start": start, "end": end})
        return dict(result.mappings().one())

    async def daily(self, start: datetime, end: datetime) -> list[dict]:
        result = await self.session.execute(text("""
            WITH days AS (
              SELECT generate_series(
                date_trunc('day', CAST(:start AS timestamptz)),
                date_trunc('day', CAST(:end AS timestamptz) - interval '1 microsecond'),
                interval '1 day'
              ) AS day
            )
            SELECT
              d.day::date::text AS day,
              (SELECT count(*) FROM calls c WHERE c.created_at >= d.day AND c.created_at < d.day + interval '1 day') AS calls,
              (SELECT count(*) FROM appointments a WHERE a.created_at >= d.day AND a.created_at < d.day + interval '1 day' AND a.status <> 'cancelled') AS appointments_booked,
              (SELECT count(*) FROM appointments a WHERE a.appointment_datetime >= d.day AND a.appointment_datetime < d.day + interval '1 day' AND a.status = 'completed') AS appointments_completed,
              (SELECT count(*) FROM appointments a WHERE a.appointment_datetime >= d.day AND a.appointment_datetime < d.day + interval '1 day' AND a.status = 'no_show') AS no_shows,
              (SELECT count(*) FROM tasks t WHERE t.updated_at >= d.day AND t.updated_at < d.day + interval '1 day' AND t.status = 'completed') AS tasks_completed,
              (SELECT count(*) FROM tasks t WHERE t.updated_at >= d.day AND t.updated_at < d.day + interval '1 day' AND t.status = 'escalated') AS escalated_tasks,
              (SELECT count(*) FROM agent_executions e WHERE e.created_at >= d.day AND e.created_at < d.day + interval '1 day') AS ai_executions,
              (SELECT count(*) FROM agent_executions e WHERE e.created_at >= d.day AND e.created_at < d.day + interval '1 day' AND e.escalation_required) AS ai_escalations,
              (SELECT count(*) FROM workflow_runs w WHERE w.completed_at >= d.day AND w.completed_at < d.day + interval '1 day' AND w.status = 'completed') AS workflows_completed,
              (SELECT count(*) FROM workflow_runs w WHERE w.updated_at >= d.day AND w.updated_at < d.day + interval '1 day' AND w.status = 'failed') AS workflows_failed,
              (SELECT count(*) FROM communications c WHERE c.created_at >= d.day AND c.created_at < d.day + interval '1 day' AND c.status IN ('sent','delivered')) AS communications_sent,
              (SELECT count(*) FROM communications c WHERE c.created_at >= d.day AND c.created_at < d.day + interval '1 day' AND c.status = 'failed') AS communications_failed
            FROM days d ORDER BY d.day
        """), {"start": start, "end": end})
        return [dict(row) for row in result.mappings().all()]

    async def financial_summary(self, start: datetime, end: datetime) -> dict:
        result = await self.session.execute(text("""
            SELECT
              (SELECT coalesce(sum(amount),0) FROM billing_charges WHERE created_at >= :start AND created_at < :end AND status <> 'voided') AS charges_amount,
              (SELECT coalesce(sum(patient_responsibility),0) FROM billing_charges WHERE created_at >= :start AND created_at < :end AND status <> 'voided') AS patient_responsibility_amount,
              (SELECT coalesce(sum(payer_responsibility),0) FROM billing_charges WHERE created_at >= :start AND created_at < :end AND status <> 'voided') AS payer_responsibility_amount,
              (SELECT coalesce(sum(amount),0) FROM billing_payments WHERE created_at >= :start AND created_at < :end AND status = 'paid') AS payments_amount,
              (SELECT coalesce(sum(billed_amount),0) FROM claims WHERE created_at >= :start AND created_at < :end AND status <> 'closed') AS claims_billed_amount,
              (SELECT coalesce(sum(paid_amount),0) FROM claims WHERE created_at >= :start AND created_at < :end) AS claims_paid_amount,
              (SELECT count(*) FROM claims WHERE created_at >= :start AND created_at < :end AND status = 'denied') AS denied_claim_count,
              (SELECT coalesce(sum(amount),0) FROM denials WHERE created_at >= :start AND created_at < :end) AS denial_amount,
              (SELECT coalesce(sum(amount),0) FROM ar_work_items WHERE created_at < :end AND status IN ('open','assigned','follow_up','escalated')) AS open_ar_amount
        """), {"start": start, "end": end})
        return dict(result.mappings().one())

    async def insurance_summary(self, start: datetime, end: datetime) -> dict:
        result = await self.session.execute(text("""
            SELECT
              (SELECT count(*) FROM eligibility_requests WHERE requested_at >= :start AND requested_at < :end) AS eligibility_requests,
              (SELECT count(*) FROM eligibility_requests WHERE responded_at >= :start AND responded_at < :end AND status = 'eligible') AS eligibility_verified,
              (SELECT count(*) FROM eligibility_requests WHERE responded_at >= :start AND responded_at < :end AND status IN ('verification_failed','failed','provider_error','unavailable','ineligible')) AS eligibility_failed,
              (SELECT count(*) FROM authorizations WHERE submitted_at >= :start AND submitted_at < :end) AS authorizations_submitted,
              (SELECT count(*) FROM authorizations WHERE response_at >= :start AND response_at < :end AND status = 'approved') AS authorizations_approved,
              (SELECT count(*) FROM authorizations WHERE response_at >= :start AND response_at < :end AND status = 'denied') AS authorizations_denied,
              (SELECT count(*) FROM referrals_v2 WHERE created_at >= :start AND created_at < :end AND status IN ('sent','received','accepted','scheduled','completed')) AS referrals_sent,
              (SELECT count(*) FROM referrals_v2 WHERE updated_at >= :start AND updated_at < :end AND status = 'completed') AS referrals_completed
        """), {"start": start, "end": end})
        return dict(result.mappings().one())

    async def compliance_summary(self, start: datetime, end: datetime) -> dict:
        result = await self.session.execute(text("""
            SELECT
              count(*) AS audit_events,
              count(*) FILTER (WHERE action IN ('integration.created','integration.connection_tested') OR action LIKE '%.manage' OR action LIKE '%.approve') AS privileged_events,
              count(*) FILTER (WHERE coalesce(agent_type,'') <> '' OR coalesce(source,'') IN ('ai','agent')) AS ai_events,
              count(*) FILTER (WHERE coalesce(resource_type,'') IN ('integration','webhook') OR coalesce(action,'') LIKE 'integration.%') AS integration_events,
              count(*) FILTER (WHERE lower(coalesce(outcome,'')) IN ('failed','error','denied','rejected')) AS failed_events
            FROM audit_log
            WHERE created_at >= :start AND created_at < :end
        """), {"start": start, "end": end})
        return dict(result.mappings().one())
