"""
Referrals Agent — specialist referral end-to-end tracking.
"""
import json
import logging
from typing import Optional, Any

from app.agents.base_agent import BaseAgent
from app.security.audit import write_audit_log

logger = logging.getLogger(__name__)


class ReferralsAgent(BaseAgent):
    """Referrals Agent — create, track, and follow up on specialist referrals."""

    agent_type: str = "referrals"

    def __init__(
        self,
        clinic_id: str,
        llm: Optional[Any] = None,
        memory: Optional[Any] = None,
        ehr: Optional[Any] = None,
    ) -> None:
        super().__init__(clinic_id=clinic_id, llm=llm, memory=memory, ehr=ehr)

    async def extract_referral_details(self, call_id: str, utterance: str) -> dict:
        """Extract specialty, reason, and urgency from speech."""
        response = await self.llm.route(
            task_type="entity_extraction",
            prompt=(
                f"Extract referral details from this utterance.\n\n"
                f"Utterance: \"{utterance}\"\n\n"
                f"Return ONLY valid JSON:\n"
                f'{{"specialty": "<specialty>", "reason": "<reason>", '
                f'"urgency": "<routine|urgent|emergent>", '
                f'"referring_provider": "<id or null>"}}'
            ),
        )
        content = response.get("content", "")
        cleaned = content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return {"specialty": "unknown", "urgency": "routine"}

    async def create_referral(
        self,
        call_id: str,
        patient_id: str,
        specialty: str,
        reason: str,
        urgency: str,
        referring_provider_id: str,
    ) -> dict:
        """Create referral packet in EHR."""
        try:
            result = await self.ehr.create_referral(
                clinic_id=self.clinic_id,
                patient_id=patient_id,
                specialty=specialty,
                reason=reason,
                urgency=urgency,
                referring_provider_id=referring_provider_id,
            )

            referral_id = result.get("referral_id")

            write_audit_log(
                event_type="referral_created",
                clinic_id=self.clinic_id,
                call_id=call_id,
                patient_id=patient_id,
                agent_type=self.agent_type,
                metadata={"referral_id": referral_id, "specialty": specialty, "urgency": urgency},
            )

            await self.memory.add_episode(
                clinic_id=self.clinic_id,
                call_id=call_id,
                episode_type="referral_created",
                content=f"Referral created: {specialty} for {reason}. Urgency: {urgency}.",
                patient_id=patient_id,
                metadata={"referral_id": referral_id, "specialty": specialty},
            )

            return {
                "success": True,
                "referral_id": referral_id,
                "status": result.get("status", "initiated"),
                "specialist": result.get("specialist"),
            }

        except Exception as e:
            logger.error("Referral creation failed: %s", str(e))
            return {"success": False, "error": str(e)}

    async def check_referral_status(self, call_id: str, referral_id: str) -> dict:
        """Check current referral status."""
        try:
            return await self.ehr.get_referral_status(
                clinic_id=self.clinic_id,
                referral_id=referral_id,
            )
        except Exception as e:
            logger.error("Referral status check failed: %s", str(e))
            return {"status": "unknown", "error": str(e)}
