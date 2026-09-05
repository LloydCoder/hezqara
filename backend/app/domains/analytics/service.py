from datetime import datetime, timezone

from app.domains.analytics.metrics import METRIC_BY_KEY
from app.domains.analytics.repository import AnalyticsRepository


class AnalyticsService:
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository

    async def summary(self, start: datetime, end: datetime) -> dict:
        raw = await self.repository.operational_summary(start, end)
        metrics = []
        for key in METRIC_BY_KEY:
            definition = METRIC_BY_KEY[key]
            metrics.append(
                {
                    "key": key,
                    "label": definition.label,
                    "value": raw.get(key),
                    "unit": definition.unit,
                    "definition": definition.definition,
                    "source_tables": list(definition.source_tables),
                }
            )
        return {"window": {"start": start, "end": end}, "metrics": metrics, "freshness": datetime.now(timezone.utc)}

    async def daily(self, start: datetime, end: datetime) -> list[dict]:
        return await self.repository.daily(start, end)

    async def financial(self, start: datetime, end: datetime) -> dict:
        raw = await self.repository.financial_summary(start, end)
        return {
            "window": {"start": start, "end": end},
            **{key: float(raw[key] or 0) if key.endswith("amount") else int(raw[key] or 0) for key in raw},
            "definitions": {
                "charges_amount": "Sum of non-voided billing charges created in the window.",
                "payments_amount": "Sum of billing payments with paid status created in the window.",
                "claims_billed_amount": "Sum of non-closed claim billed amounts created in the window.",
                "claims_paid_amount": "Sum of claim paid amounts for claims created in the window.",
                "denial_amount": "Sum of denial amounts created in the window.",
                "open_ar_amount": "Sum of currently open A/R work-item amounts visible at the end of the window.",
            },
            "source_tables": ["billing_charges", "billing_payments", "claims", "denials", "ar_work_items"],
        }

    async def insurance(self, start: datetime, end: datetime) -> dict:
        raw = await self.repository.insurance_summary(start, end)
        return {
            "window": {"start": start, "end": end},
            **{key: int(raw[key] or 0) for key in raw},
            "definitions": {
                "eligibility_verified": "Eligibility requests with an eligible response in the window.",
                "eligibility_failed": "Eligibility responses classified as ineligible, unavailable, provider error, failed, or verification failed.",
                "authorizations_submitted": "Authorizations with a submission timestamp in the window.",
                "authorizations_approved": "Authorizations receiving approved status in the window.",
                "authorizations_denied": "Authorizations receiving denied status in the window.",
            },
            "source_tables": ["eligibility_requests", "authorizations", "referrals_v2"],
        }

    async def compliance(self, start: datetime, end: datetime) -> dict:
        raw = await self.repository.compliance_summary(start, end)
        return {
            "window": {"start": start, "end": end},
            **{key: int(raw[key] or 0) for key in raw},
            "definitions": {
                "audit_events": "Audit-log events created in the reporting window.",
                "privileged_events": "Audit events matching the platform's currently classified privileged actions.",
                "ai_events": "Audit events carrying an AI/agent source or agent type.",
                "integration_events": "Audit events associated with integration resources or integration actions.",
                "failed_events": "Audit events explicitly classified as failed, error, denied, or rejected.",
            },
            "source_tables": ["audit_log"],
        }
