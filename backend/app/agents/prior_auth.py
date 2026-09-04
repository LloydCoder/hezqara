"""
Prior Auth Agent — prior authorization submission and tracking.

CMS-0057-F mandate: payers must respond within 72 hours (Jan 2027).
This agent automates the full PA lifecycle.

Clinical reasoning routes to Parliament Ensemble (Claude Sonnet)
— the only agent that consistently needs expensive LLM calls.
Everything else uses local models.
"""
import json
import logging
from typing import Optional, Any

from app.agents.base_agent import BaseAgent
from app.security.audit import write_audit_log

logger = logging.getLogger(__name__)


class PriorAuthAgent(BaseAgent):
    """Prior Auth Agent — PA submission, tracking, and clinical reasoning."""

    agent_type: str = "prior_auth"

    def __init__(
        self,
        clinic_id: str,
        llm: Optional[Any] = None,
        memory: Optional[Any] = None,
        ehr: Optional[Any] = None,
        insurance_client: Optional[Any] = None,
        payer_client: Optional[Any] = None,
    ) -> None:
        super().__init__(clinic_id=clinic_id, llm=llm, memory=memory, ehr=ehr)
        self.insurance_client = insurance_client
        self.payer_client = payer_client

    # ── Requirement check ─────────────────────────────────────────────────────

    async def check_pa_requirement(
        self,
        call_id: str,
        service_code: str,
        member_id: str,
        diagnosis_code: str,
    ) -> dict:
        """Check whether service requires prior authorization."""
        try:
            return await self.insurance_client.check_pa_requirement(
                clinic_id=self.clinic_id,
                service_code=service_code,
                member_id=member_id,
                diagnosis_code=diagnosis_code,
            )
        except Exception as e:
            logger.error("PA requirement check failed: %s", str(e))
            return {"required": None, "error": str(e)}

    # ── Submission ────────────────────────────────────────────────────────────

    async def submit_pa_request(
        self,
        call_id: str,
        pa_data: dict,
    ) -> dict:
        """Submit PA request to payer via FHIR Da Vinci PAS."""
        try:
            result = await self.payer_client.submit_prior_auth(
                clinic_id=self.clinic_id,
                pa_data=pa_data,
            )

            tracking_number = result.get("tracking_number")

            write_audit_log(
                event_type="prior_auth_submitted",
                clinic_id=self.clinic_id,
                call_id=call_id,
                patient_id=pa_data.get("patient_id"),
                agent_type=self.agent_type,
                metadata={
                    "tracking_number": tracking_number,
                    "service_code": pa_data.get("service_code"),
                },
            )

            await self.memory.add_episode(
                clinic_id=self.clinic_id,
                call_id=call_id,
                episode_type="prior_auth_submitted",
                content=f"PA submitted for service {pa_data.get('service_code')}. Tracking: {tracking_number}.",
                patient_id=pa_data.get("patient_id"),
                metadata={"tracking_number": tracking_number, "status": result.get("status")},
            )

            return {
                "success": True,
                "tracking_number": tracking_number,
                "status": result.get("status", "pending"),
            }

        except Exception as e:
            logger.error("PA submission failed for call %s: %s", call_id, str(e))
            return {"success": False, "error": str(e)}

    # ── Status polling ────────────────────────────────────────────────────────

    async def check_pa_status(
        self,
        call_id: str,
        tracking_number: str,
    ) -> dict:
        """Poll payer for PA decision."""
        try:
            return await self.payer_client.get_pa_status(
                clinic_id=self.clinic_id,
                tracking_number=tracking_number,
            )
        except Exception as e:
            logger.error("PA status check failed for %s: %s", tracking_number, str(e))
            return {"status": "unknown", "error": str(e)}

    # ── Clinical reasoning — Parliament Ensemble ──────────────────────────────

    async def generate_clinical_justification(
        self,
        call_id: str,
        service_code: str,
        diagnosis_codes: list,
        clinical_notes: str,
    ) -> dict:
        """
        Generate clinical justification for PA request.
        Routes to Parliament Ensemble (Claude Sonnet) —
        this is genuine clinical reasoning, not routine extraction.
        """
        response = await self.llm.route(
            task_type="prior_auth_clinical",
            prompt=(
                f"Generate clinical justification for a prior authorization request.\n\n"
                f"Service: {service_code}\n"
                f"Diagnoses: {', '.join(diagnosis_codes)}\n"
                f"Clinical notes: {clinical_notes}\n\n"
                f"Provide medical necessity rationale aligned with payer criteria. "
                f"Return JSON: {{\"recommendation\": \"approve|deny|more_info\", "
                f"\"clinical_basis\": \"<rationale>\"}}"
            ),
        )

        content = response.get("content", "")
        try:
            cleaned = content.strip().lstrip("```json").rstrip("```").strip()
            return json.loads(cleaned)
        except Exception:
            return {"recommendation": "more_info", "clinical_basis": content}
