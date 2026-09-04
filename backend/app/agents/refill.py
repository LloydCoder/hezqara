"""
Refill Agent — medication refill request handling.

Parses refill requests, checks eligibility, routes controlled
substances to provider, sends approved refills to pharmacy,
and notifies patient of outcome.

Cost discipline:
  - Medication extraction → local Ollama (deepseek-coder-v2)
  - Confirmation text    → local Ollama (refill_request_parse task)
  - Never needs Claude
"""
import json
import logging
from typing import Optional, Any

from app.agents.base_agent import BaseAgent
from app.security.audit import write_audit_log

logger = logging.getLogger(__name__)

# Controlled substance schedules requiring provider approval
CONTROLLED_SCHEDULES = {"II", "III", "IV", "V"}


class RefillAgent(BaseAgent):
    """Refill Agent — medication refill end-to-end."""

    agent_type: str = "refill"

    def __init__(
        self,
        clinic_id: str,
        llm: Optional[Any] = None,
        memory: Optional[Any] = None,
        ehr: Optional[Any] = None,
    ) -> None:
        super().__init__(clinic_id=clinic_id, llm=llm, memory=memory, ehr=ehr)

    async def extract_refill_request(self, call_id: str, utterance: str) -> dict:
        """Extract medication, dose, and pharmacy from speech."""
        response = await self.llm.route(
            task_type="refill_request_parse",
            prompt=(
                f"Extract refill request details from this utterance.\n\n"
                f"Utterance: \"{utterance}\"\n\n"
                f"Return ONLY valid JSON:\n"
                f'{{"medication": "<name>", "dose": "<dose or null>", '
                f'"pharmacy": "<name or null>", "days_supply": <30|60|90|null>}}'
            ),
        )
        return self._parse_json(response.get("content", ""))

    async def check_refill_eligibility(
        self, call_id: str, patient_id: str, medication: str
    ) -> dict:
        """Check if patient is eligible for refill."""
        try:
            result = await self.ehr.check_refill_eligibility(
                clinic_id=self.clinic_id,
                patient_id=patient_id,
                medication=medication,
            )
            # Controlled substances always need provider approval
            if result.get("controlled_substance"):
                result["requires_provider_approval"] = True
            return result
        except Exception as e:
            logger.error("Refill eligibility check failed: %s", str(e))
            return {"eligible": None, "error": str(e)}

    async def process_refill(
        self,
        call_id: str,
        patient_id: str,
        medication: str,
        dose: str,
        pharmacy: str,
    ) -> dict:
        """Send approved refill to pharmacy electronically."""
        try:
            result = await self.ehr.send_refill_to_pharmacy(
                clinic_id=self.clinic_id,
                patient_id=patient_id,
                medication=medication,
                dose=dose,
                pharmacy=pharmacy,
            )

            write_audit_log(
                event_type="refill_processed",
                clinic_id=self.clinic_id,
                call_id=call_id,
                patient_id=patient_id,
                agent_type=self.agent_type,
                metadata={"medication": medication, "pharmacy": pharmacy},
            )

            await self.memory.add_episode(
                clinic_id=self.clinic_id,
                call_id=call_id,
                episode_type="refill_sent",
                content=f"Refill sent: {medication} {dose} to {pharmacy}.",
                patient_id=patient_id,
                metadata={"medication": medication, "refill_id": result.get("refill_id")},
            )

            return {
                "success": True,
                "refill_id": result.get("refill_id"),
                "status": result.get("status", "sent"),
                "pharmacy": pharmacy,
                "estimated_ready": result.get("estimated_ready"),
            }

        except Exception as e:
            logger.error("Refill processing failed: %s", str(e))
            return {"success": False, "error": str(e)}

    async def generate_refill_confirmation(
        self, medication: str, pharmacy: str, estimated_ready: str
    ) -> str:
        """Generate patient confirmation message."""
        response = await self.llm.route(
            task_type="refill_request_parse",
            prompt=(
                f"Generate a brief confirmation that a refill was sent.\n"
                f"Medication: {medication}\nPharmacy: {pharmacy}\n"
                f"Ready: {estimated_ready}\nKeep under 25 words."
            ),
        )
        return response.get("content", f"Your {medication} refill has been sent to {pharmacy}.")

    def _parse_json(self, content: str) -> dict:
        if not content:
            return {}
        cleaned = content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {}
