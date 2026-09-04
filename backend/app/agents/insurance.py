"""
Insurance Agent — payer-facing eligibility and benefits.

Handles all insurance interactions:
  - Real-time eligibility verification via Availity
  - Benefits check (copay, deductible, OOP max)
  - In-network/out-of-network status
  - Plain-language coverage explanation to patient
  - Financial counselling flags
  - HIPAA audit logging
  - Graphiti episode storage
"""
import json
import logging
from typing import Optional, Any

from app.agents.base_agent import BaseAgent
from app.security.audit import write_audit_log

logger = logging.getLogger(__name__)


class InsuranceAgent(BaseAgent):
    """Insurance Agent — real-time eligibility and benefits."""

    agent_type: str = "insurance"

    def __init__(
        self,
        clinic_id: str,
        llm: Optional[Any] = None,
        memory: Optional[Any] = None,
        ehr: Optional[Any] = None,
        insurance_client: Optional[Any] = None,
    ) -> None:
        super().__init__(clinic_id=clinic_id, llm=llm, memory=memory, ehr=ehr)
        self.insurance_client = insurance_client

    # ── Eligibility ───────────────────────────────────────────────────────────

    async def verify_eligibility(
        self,
        call_id: str,
        patient_id: str,
        member_id: str,
        date_of_service: str,
    ) -> dict:
        """Verify insurance eligibility via Availity API."""
        try:
            result = await self.insurance_client.check_eligibility(
                clinic_id=self.clinic_id,
                member_id=member_id,
                date_of_service=date_of_service,
            )

            write_audit_log(
                event_type="eligibility_checked",
                clinic_id=self.clinic_id,
                call_id=call_id,
                patient_id=patient_id,
                agent_type=self.agent_type,
                metadata={"eligible": result.get("eligible"), "member_id_masked": member_id[:4] + "****"},
            )

            await self.memory.add_episode(
                clinic_id=self.clinic_id,
                call_id=call_id,
                episode_type="eligibility_verified",
                content=f"Eligibility: {'active' if result.get('eligible') else 'inactive'}. Carrier: {result.get('carrier', 'unknown')}.",
                patient_id=patient_id,
                metadata={"eligible": result.get("eligible"), "carrier": result.get("carrier")},
            )

            return result

        except Exception as e:
            logger.error("Eligibility check failed for %s: %s", member_id[:4], str(e))
            return {"eligible": None, "error": str(e)}

    # ── Benefits ──────────────────────────────────────────────────────────────

    async def get_benefits(
        self,
        call_id: str,
        member_id: str,
        service_type: str,
    ) -> dict:
        """Fetch copay, deductible, and OOP status."""
        try:
            return await self.insurance_client.get_benefits(
                clinic_id=self.clinic_id,
                member_id=member_id,
                service_type=service_type,
            )
        except Exception as e:
            logger.error("Benefits check failed: %s", str(e))
            return {"error": str(e)}

    async def check_network_status(
        self,
        call_id: str,
        provider_id: str,
        member_id: str,
    ) -> dict:
        """Check whether provider is in-network for this plan."""
        try:
            return await self.insurance_client.check_network_status(
                clinic_id=self.clinic_id,
                provider_id=provider_id,
                member_id=member_id,
            )
        except Exception as e:
            logger.error("Network check failed: %s", str(e))
            return {"in_network": None, "error": str(e)}

    # ── Patient communication ─────────────────────────────────────────────────

    async def explain_coverage_to_patient(
        self,
        call_id: str,
        benefits: dict,
    ) -> str:
        """Generate plain-language coverage explanation."""
        response = await self.llm.route(
            task_type="insurance_code_lookup",
            prompt=(
                f"Explain this insurance coverage to a patient in plain, "
                f"friendly language. Be specific about dollar amounts.\n\n"
                f"Benefits: {json.dumps(benefits)}\n\n"
                f"Keep it under 40 words. No jargon."
            ),
        )
        return response.get("content", "Your coverage details have been verified.")

    def assess_financial_counselling_need(self, benefits: dict) -> dict:
        """Flag patients who may need financial counselling."""
        needs = False
        reason = None

        if benefits.get("uninsured") or benefits.get("eligible") is False:
            needs = True
            reason = "No active insurance coverage"
        elif benefits.get("out_of_pocket_met", 0) == 0 and benefits.get("deductible_annual", 0) > 3000:
            needs = True
            reason = "High deductible plan with no deductible met"

        return {"needs_counselling": needs, "reason": reason}
