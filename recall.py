"""
Recall Agent — proactive patient outreach to fill the schedule.

Generates the most revenue per clinic by turning dormant patients
into booked appointments. SMS/email/voice/WhatsApp channels.

Cost discipline:
  - Message generation → local Ollama (qwen2.5:14b)
  - Response classification → local Ollama (deepseek-coder-v2)
  - Never needs Claude
"""
import json
import logging
from typing import Optional, Any

from app.agents.base_agent import BaseAgent
from app.security.audit import write_audit_log

logger = logging.getLogger(__name__)

RECALL_TASK_TYPE = "recall_sms_generate"


class RecallAgent(BaseAgent):
    """Recall Agent — proactive patient outreach campaigns."""

    agent_type: str = "recall"

    def __init__(
        self,
        clinic_id: str,
        llm: Optional[Any] = None,
        memory: Optional[Any] = None,
        ehr: Optional[Any] = None,
        sms_client: Optional[Any] = None,
        email_client: Optional[Any] = None,
    ) -> None:
        super().__init__(clinic_id=clinic_id, llm=llm, memory=memory, ehr=ehr)
        self.sms_client = sms_client
        self.email_client = email_client

    async def identify_overdue_patients(
        self, recall_type: str, months_overdue: int
    ) -> list:
        """Identify patients overdue for a specific type of care."""
        try:
            return await self.ehr.get_overdue_patients(
                clinic_id=self.clinic_id,
                recall_type=recall_type,
                months_overdue=months_overdue,
            )
        except Exception as e:
            logger.error("Overdue patient identification failed: %s", str(e))
            return []

    async def generate_recall_message(
        self,
        patient_name: str,
        clinic_name: str,
        recall_type: str,
        channel: str,
    ) -> str:
        """Generate personalized recall message for patient."""
        channel_instruction = (
            "Keep under 160 characters." if channel == "sms"
            else "Write a friendly 2-3 sentence email."
        )

        response = await self.llm.route(
            task_type=RECALL_TASK_TYPE,
            prompt=(
                f"Generate a {channel} recall message.\n"
                f"Patient: {patient_name}\n"
                f"Clinic: {clinic_name}\n"
                f"Recall type: {recall_type}\n"
                f"{channel_instruction}\n"
                f"Be warm, clear, and include a call to action."
            ),
        )
        return response.get("content", f"Hi {patient_name}! {clinic_name} would like to schedule your {recall_type}.")

    async def send_recall_sms(
        self,
        patient_id: str,
        phone: str,
        message: str,
    ) -> dict:
        """Send recall via SMS."""
        try:
            result = await self.sms_client.send_sms(to=phone, body=message)

            write_audit_log(
                event_type="recall_sent",
                clinic_id=self.clinic_id,
                patient_id=patient_id,
                agent_type=self.agent_type,
                metadata={"channel": "sms", "message_id": result.get("message_id")},
            )

            await self.memory.add_episode(
                clinic_id=self.clinic_id,
                call_id=None,
                episode_type="recall_sent",
                content=f"Recall SMS sent to patient.",
                patient_id=patient_id,
                metadata={"channel": "sms", "message_id": result.get("message_id")},
            )

            return {"status": result.get("status", "sent"), "message_id": result.get("message_id")}

        except Exception as e:
            logger.error("SMS recall failed for patient %s: %s", patient_id, str(e))
            return {"status": "failed", "error": str(e)}

    async def handle_recall_response(
        self, patient_id: str, response_text: str
    ) -> dict:
        """Classify patient's response to recall message."""
        response = await self.llm.route(
            task_type="intent_detection",
            prompt=(
                f"Classify this patient response to a recall message.\n\n"
                f"Response: \"{response_text}\"\n\n"
                f"Return ONLY valid JSON:\n"
                f'{{"response": "<positive|negative|maybe>", '
                f'"action": "<schedule|declined|follow_up>"}}'
            ),
        )
        content = response.get("content", "")
        cleaned = content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return {"response": "unknown", "action": "follow_up"}
