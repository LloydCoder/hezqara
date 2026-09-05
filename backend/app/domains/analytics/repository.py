from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class AnalyticsRepository:
    def __init__(self, session: AsyncSession): self.session=session
    async def operational_summary(self,start:datetime,end:datetime)->dict:
        result=await self.session.execute(text("""SELECT
          (SELECT count(*) FROM calls WHERE created_at>=:start AND created_at<:end) calls,
          (SELECT count(*) FROM appointments WHERE created_at>=:start AND created_at<:end AND status<>'cancelled') appointments_booked,
          (SELECT count(*) FROM appointments WHERE appointment_datetime>=:start AND appointment_datetime<:end AND status='completed') appointments_completed,
          (SELECT count(*) FROM appointments WHERE appointment_datetime>=:start AND appointment_datetime<:end AND status='no_show') no_shows,
          (SELECT count(*) FROM tasks WHERE updated_at>=:start AND updated_at<:end AND status='completed') tasks_completed,
          (SELECT count(*) FROM tasks WHERE updated_at>=:start AND updated_at<:end AND status='escalated') escalated_tasks,
          (SELECT count(*) FROM agent_executions WHERE created_at>=:start AND created_at<:end) ai_executions,
          (SELECT count(*) FROM agent_executions WHERE created_at>=:start AND created_at<:end AND escalation_required) ai_escalations,
          (SELECT count(*) FROM workflow_runs WHERE completed_at>=:start AND completed_at<:end AND status='completed') workflows_completed,
          (SELECT count(*) FROM workflow_runs WHERE updated_at>=:start AND updated_at<:end AND status='failed') workflows_failed,
          (SELECT count(*) FROM communications WHERE created_at>=:start AND created_at<:end AND status IN ('sent','delivered')) communications_sent,
          (SELECT count(*) FROM communications WHERE created_at>=:start AND created_at<:end AND status='failed') communications_failed"""),{"start":start,"end":end});return dict(result.mappings().one())
    async def daily(self,start:datetime,end:datetime)->list[dict]:
        result=await self.session.execute(text("""WITH days AS (SELECT generate_series(date_trunc('day',CAST(:start AS timestamptz)),date_trunc('day',CAST(:end AS timestamptz)-interval '1 microsecond'),interval '1 day') day),
        c AS (SELECT date_trunc('day',created_at) day,count(*) value FROM calls WHERE created_at>=:start AND created_at<:end GROUP BY 1),
        ab AS (SELECT date_trunc('day',created_at) day,count(*) value FROM appointments WHERE created_at>=:start AND created_at<:end AND status<>'cancelled' GROUP BY 1),
        ac AS (SELECT date_trunc('day',appointment_datetime) day,count(*) value FROM appointments WHERE appointment_datetime>=:start AND appointment_datetime<:end AND status='completed' GROUP BY 1),
        ns AS (SELECT date_trunc('day',appointment_datetime) day,count(*) value FROM appointments WHERE appointment_datetime>=:start AND appointment_datetime<:end AND status='no_show' GROUP BY 1),
        tc AS (SELECT date_trunc('day',updated_at) day,count(*) value FROM tasks WHERE updated_at>=:start AND updated_at<:end AND status='completed' GROUP BY 1),
        te AS (SELECT date_trunc('day',updated_at) day,count(*) value FROM tasks WHERE updated_at>=:start AND updated_at<:end AND status='escalated' GROUP BY 1),
        ae AS (SELECT date_trunc('day',created_at) day,count(*) value,count(*) FILTER(WHERE escalation_required) escalations FROM agent_executions WHERE created_at>=:start AND created_at<:end GROUP BY 1),
        wc AS (SELECT date_trunc('day',completed_at) day,count(*) value FROM workflow_runs WHERE completed_at>=:start AND completed_at<:end AND status='completed' GROUP BY 1),
        wf AS (SELECT date_trunc('day',updated_at) day,count(*) value FROM workflow_runs WHERE updated_at>=:start AND updated_at<:end AND status='failed' GROUP BY 1),
        cs AS (SELECT date_trunc('day',created_at) day,count(*) value FROM communications WHERE created_at>=:start AND created_at<:end AND status IN('sent','delivered') GROUP BY 1),
        cf AS (SELECT date_trunc('day',created_at) day,count(*) value FROM communications WHERE created_at>=:start AND created_at<:end AND status='failed' GROUP BY 1),
        ch AS (SELECT date_trunc('day',created_at) day,coalesce(sum(amount),0) value FROM billing_charges WHERE created_at>=:start AND created_at<:end AND status<>'voided' GROUP BY 1),
        pm AS (SELECT date_trunc('day',created_at) day,coalesce(sum(amount),0) value FROM billing_payments WHERE created_at>=:start AND created_at<:end AND status='paid' GROUP BY 1),
        dn AS (SELECT date_trunc('day',created_at) day,coalesce(sum(amount),0) value FROM denials WHERE created_at>=:start AND created_at<:end GROUP BY 1),
        er AS (SELECT date_trunc('day',requested_at) day,count(*) value FROM eligibility_requests WHERE requested_at>=:start AND requested_at<:end GROUP BY 1),
        ef AS (SELECT date_trunc('day',responded_at) day,count(*) value FROM eligibility_requests WHERE responded_at>=:start AND responded_at<:end AND status IN('verification_failed','failed','provider_error','unavailable','ineligible') GROUP BY 1),
        au AS (SELECT date_trunc('day',submitted_at) day,count(*) value FROM authorizations WHERE submitted_at>=:start AND submitted_at<:end GROUP BY 1),
        ad AS (SELECT date_trunc('day',response_at) day,count(*) value FROM authorizations WHERE response_at>=:start AND response_at<:end AND status='denied' GROUP BY 1),
        rc AS (SELECT date_trunc('day',updated_at) day,count(*) value FROM referrals_v2 WHERE updated_at>=:start AND updated_at<:end AND status='completed' GROUP BY 1)
        SELECT d.day::date::text day,coalesce(c.value,0)::int calls,coalesce(ab.value,0)::int appointments_booked,coalesce(ac.value,0)::int appointments_completed,coalesce(ns.value,0)::int no_shows,coalesce(tc.value,0)::int tasks_completed,coalesce(te.value,0)::int escalated_tasks,coalesce(ae.value,0)::int ai_executions,coalesce(ae.escalations,0)::int ai_escalations,coalesce(wc.value,0)::int workflows_completed,coalesce(wf.value,0)::int workflows_failed,coalesce(cs.value,0)::int communications_sent,coalesce(cf.value,0)::int communications_failed,coalesce(ch.value,0)::float charges_amount,coalesce(pm.value,0)::float payments_amount,coalesce(dn.value,0)::float denial_amount,coalesce(er.value,0)::int eligibility_requests,coalesce(ef.value,0)::int eligibility_failed,coalesce(au.value,0)::int authorizations_submitted,coalesce(ad.value,0)::int authorizations_denied,coalesce(rc.value,0)::int referrals_completed
        FROM days d LEFT JOIN c ON c.day=d.day LEFT JOIN ab ON ab.day=d.day LEFT JOIN ac ON ac.day=d.day LEFT JOIN ns ON ns.day=d.day LEFT JOIN tc ON tc.day=d.day LEFT JOIN te ON te.day=d.day LEFT JOIN ae ON ae.day=d.day LEFT JOIN wc ON wc.day=d.day LEFT JOIN wf ON wf.day=d.day LEFT JOIN cs ON cs.day=d.day LEFT JOIN cf ON cf.day=d.day LEFT JOIN ch ON ch.day=d.day LEFT JOIN pm ON pm.day=d.day LEFT JOIN dn ON dn.day=d.day LEFT JOIN er ON er.day=d.day LEFT JOIN ef ON ef.day=d.day LEFT JOIN au ON au.day=d.day LEFT JOIN ad ON ad.day=d.day LEFT JOIN rc ON rc.day=d.day ORDER BY d.day"""),{"start":start,"end":end});return [dict(r) for r in result.mappings().all()]
    async def financial_summary(self,start:datetime,end:datetime)->dict:
        result=await self.session.execute(text("""SELECT
          (SELECT coalesce(sum(amount),0) FROM billing_charges WHERE created_at>=:start AND created_at<:end AND status<>'voided') charges_amount,
          (SELECT coalesce(sum(patient_responsibility),0) FROM billing_charges WHERE created_at>=:start AND created_at<:end AND status<>'voided') patient_responsibility_amount,
          (SELECT coalesce(sum(payer_responsibility),0) FROM billing_charges WHERE created_at>=:start AND created_at<:end AND status<>'voided') payer_responsibility_amount,
          (SELECT coalesce(sum(amount),0) FROM billing_payments WHERE created_at>=:start AND created_at<:end AND status='paid') payments_amount,
          (SELECT coalesce(sum(billed_amount),0) FROM claims WHERE created_at>=:start AND created_at<:end AND status<>'closed') claims_billed_amount,
          (SELECT coalesce(sum(paid_amount),0) FROM claims WHERE created_at>=:start AND created_at<:end) claims_paid_amount,
          (SELECT count(*) FROM claims WHERE created_at>=:start AND created_at<:end) claim_count,
          (SELECT count(*) FROM claims WHERE created_at>=:start AND created_at<:end AND status='denied') denied_claim_count,
          (SELECT coalesce(sum(amount),0) FROM denials WHERE created_at>=:start AND created_at<:end) denial_amount,
          (SELECT coalesce(sum(amount),0) FROM ar_work_items WHERE created_at<:end AND status IN('open','assigned','follow_up','escalated')) open_ar_amount"""),{"start":start,"end":end});return dict(result.mappings().one())
    async def insurance_summary(self,start:datetime,end:datetime)->dict:
        result=await self.session.execute(text("""SELECT
          (SELECT count(*) FROM eligibility_requests WHERE requested_at>=:start AND requested_at<:end) eligibility_requests,
          (SELECT count(*) FROM eligibility_requests WHERE responded_at>=:start AND responded_at<:end AND status='eligible') eligibility_verified,
          (SELECT count(*) FROM eligibility_requests WHERE responded_at>=:start AND responded_at<:end AND status IN('verification_failed','failed','provider_error','unavailable','ineligible')) eligibility_failed,
          (SELECT count(*) FROM authorizations WHERE submitted_at>=:start AND submitted_at<:end) authorizations_submitted,
          (SELECT count(*) FROM authorizations WHERE response_at>=:start AND response_at<:end AND status='approved') authorizations_approved,
          (SELECT count(*) FROM authorizations WHERE response_at>=:start AND response_at<:end AND status='denied') authorizations_denied,
          (SELECT count(*) FROM referrals_v2 WHERE created_at>=:start AND created_at<:end AND status IN('sent','received','accepted','scheduled','completed')) referrals_sent,
          (SELECT count(*) FROM referrals_v2 WHERE updated_at>=:start AND updated_at<:end AND status='completed') referrals_completed"""),{"start":start,"end":end});return dict(result.mappings().one())
    async def compliance_summary(self,start:datetime,end:datetime)->dict:
        result=await self.session.execute(text("""SELECT count(*) audit_events,count(*) FILTER(WHERE action IN('integration.created','integration.connection_tested') OR action LIKE '%.manage' OR action LIKE '%.approve') privileged_events,count(*) FILTER(WHERE coalesce(agent_type,'')<>'' OR coalesce(metadata->>'source','') IN('ai','agent')) ai_events,count(*) FILTER(WHERE coalesce(metadata->>'resource_type','') IN('integration','webhook') OR coalesce(action,'') LIKE 'integration.%') integration_events,count(*) FILTER(WHERE lower(coalesce(metadata->>'outcome','')) IN('failed','error','denied','rejected')) failed_events FROM audit_log WHERE created_at>=:start AND created_at<:end"""),{"start":start,"end":end});return dict(result.mappings().one())
    async def compliance_evidence(self,start:datetime,end:datetime,limit:int,offset:int,action:str|None=None,outcome:str|None=None)->tuple[list[dict],int]:
        filters="created_at>=:start AND created_at<:end";params={"start":start,"end":end,"limit":limit,"offset":offset}
        if action:filters+=" AND action=:action";params["action"]=action
        if outcome:filters+=" AND lower(coalesce(metadata->>'outcome',''))=lower(:outcome)";params["outcome"]=outcome
        result=await self.session.execute(text(f"""SELECT id::text id,created_at,action,coalesce(metadata->>'resource_type','audit') resource_type,coalesce(metadata->>'resource_id',null) resource_id,coalesce(metadata->>'outcome','recorded') outcome,nullif(agent_type,'') agent_type,nullif(metadata->>'request_id','') request_id,'{{}}'::jsonb metadata,count(*) OVER() total FROM audit_log WHERE {filters} ORDER BY created_at DESC LIMIT :limit OFFSET :offset"""),params);rows=[dict(r) for r in result.mappings().all()];total=int(rows[0].pop('total') if rows else 0);return rows,total
    async def metric_trace(self,key:str,start:datetime,end:datetime,limit:int=366)->list[dict]:
        queries={
          "calls":("calls","created_at","SELECT date_trunc('day',created_at)::date::text day,NULL::text status,count(*)::int count,NULL::float amount FROM calls WHERE created_at>=:start AND created_at<:end GROUP BY 1 ORDER BY 1 DESC LIMIT :limit"),
          "appointments_booked":("appointments","created_at","SELECT date_trunc('day',created_at)::date::text day,status,count(*)::int count,NULL::float amount FROM appointments WHERE created_at>=:start AND created_at<:end AND status<>'cancelled' GROUP BY 1,status ORDER BY 1 DESC LIMIT :limit"),
          "tasks_completed":("tasks","updated_at","SELECT date_trunc('day',updated_at)::date::text day,status,count(*)::int count,NULL::float amount FROM tasks WHERE updated_at>=:start AND updated_at<:end AND status='completed' GROUP BY 1,status ORDER BY 1 DESC LIMIT :limit"),
          "ai_executions":("agent_executions","created_at","SELECT date_trunc('day',created_at)::date::text day,status,count(*)::int count,NULL::float amount FROM agent_executions WHERE created_at>=:start AND created_at<:end GROUP BY 1,status ORDER BY 1 DESC LIMIT :limit"),
          "workflows_completed":("workflow_runs","completed_at","SELECT date_trunc('day',completed_at)::date::text day,status,count(*)::int count,NULL::float amount FROM workflow_runs WHERE completed_at>=:start AND completed_at<:end AND status='completed' GROUP BY 1,status ORDER BY 1 DESC LIMIT :limit"),
          "charges_amount":("billing_charges","created_at","SELECT date_trunc('day',created_at)::date::text day,status,count(*)::int count,coalesce(sum(amount),0)::float amount FROM billing_charges WHERE created_at>=:start AND created_at<:end AND status<>'voided' GROUP BY 1,status ORDER BY 1 DESC LIMIT :limit"),
          "payments_amount":("billing_payments","created_at","SELECT date_trunc('day',created_at)::date::text day,status,count(*)::int count,coalesce(sum(amount),0)::float amount FROM billing_payments WHERE created_at>=:start AND created_at<:end AND status='paid' GROUP BY 1,status ORDER BY 1 DESC LIMIT :limit"),
          "denial_amount":("denials","created_at","SELECT date_trunc('day',created_at)::date::text day,NULL::text status,count(*)::int count,coalesce(sum(amount),0)::float amount FROM denials WHERE created_at>=:start AND created_at<:end GROUP BY 1 ORDER BY 1 DESC LIMIT :limit"),
          "eligibility_requests":("eligibility_requests","requested_at","SELECT date_trunc('day',requested_at)::date::text day,status,count(*)::int count,NULL::float amount FROM eligibility_requests WHERE requested_at>=:start AND requested_at<:end GROUP BY 1,status ORDER BY 1 DESC LIMIT :limit"),
          "authorizations_submitted":("authorizations","submitted_at","SELECT date_trunc('day',submitted_at)::date::text day,status,count(*)::int count,NULL::float amount FROM authorizations WHERE submitted_at>=:start AND submitted_at<:end GROUP BY 1,status ORDER BY 1 DESC LIMIT :limit"),
          "referrals_completed":("referrals_v2","updated_at","SELECT date_trunc('day',updated_at)::date::text day,status,count(*)::int count,NULL::float amount FROM referrals_v2 WHERE updated_at>=:start AND updated_at<:end AND status='completed' GROUP BY 1,status ORDER BY 1 DESC LIMIT :limit"),
          "audit_events":("audit_log","created_at","SELECT date_trunc('day',created_at)::date::text day,NULL::text status,count(*)::int count,NULL::float amount FROM audit_log WHERE created_at>=:start AND created_at<:end GROUP BY 1 ORDER BY 1 DESC LIMIT :limit")}
        if key not in queries:return []
        table,time_field,sql=queries[key];result=await self.session.execute(text(sql),{"start":start,"end":end,"limit":min(max(limit,1),366)});return [{"source_table":table,"time_field":time_field,**dict(r)} for r in result.mappings().all()]
