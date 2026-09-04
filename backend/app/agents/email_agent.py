"""
Email Agent — clinic inbox management via Resend.

Categorizes, drafts, and sends emails.
Clinical questions always flagged for provider review.
Never sends unsupervised medical advice.

Cost discipline:
  - Categorization → local Ollama (deepseek-coder-v2)
  - Draft generation → local Ollama (qwen2.5:14b)
  - Never needs Claude for email tasks
"""
import json
import logging
from typing import Optional, Any

from app.agents.base_agent import BaseAgent
from app.security.audit import write_audit_log

logger = logging.getLogger(__name__)

# Categories that always require provider review before sending
PROVIDER_REQUIRED_CATEGORIES = {
    "clinical_question",
    "test_results",
    "medication_change",
    "symptom_report",
}


class EmailAgent(BaseAgent):
    """Email Agent — inbox triage, drafting, and sending via Resend."""

    agent_type: str = "email"

    def __init__(
        self,
        clinic_id: str,
        llm: Optional[Any] = None,
        memory: Optional[Any] = None,
        ehr: Optional[Any] = None,
        email_client: Optional[Any] = None,
    ) -> None:
        super().__init__(clinic_id=clinic_id, llm=llm, memory=memory, ehr=ehr)
        self.email_client = email_client

    async def categorize_email(
        self,
        call_id: str,
        subject: str,
        body: str,
    ) -> dict:
        """Categorize email by intent and urgency."""
        response = await self.llm.route(
            task_type="email_categorize",
            prompt=(
                f"Categorize this patient email.\n\n"
                f"Subject: {subject}\n"
                f"Body: {body}\n\n"
                f"Return ONLY valid JSON:\n"
                f'{{"category": "<appointment_request|clinical_question|refill_request|'
                f'records_request|billing|general|urgent>", '
                f'"urgency": "<routine|urgent|emergent>", '
                f'"requires_provider": <true|false>}}'
            ),
        )
        content = response.get("content", "")
        cleaned = content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        try:
            result = json.loads(cleaned)
            # Safety override — clinical categories always require provider
            if result.get("category") in PROVIDER_REQUIRED_CATEGORIES:
                result["requires_provider"] = True
            return result
        except Exception:
            return {"category": "general", "urgency": "routine", "requires_provider": False}

    async def draft_reply(
        self,
        call_id: str,
        category: str,
        context: dict,
    ) -> str:
        """Draft email reply based on category and context."""
        disclaimer = (
            " Please note this message is for informational purposes only "
            "and does not constitute medical advice."
            if category in PROVIDER_REQUIRED_CATEGORIES else ""
        )

        response = await self.llm.route(
            task_type="email_categorize",
            prompt=(
                f"Draft a professional, warm email reply.\n\n"
                f"Category: {category}\n"
                f"Context: {json.dumps(context)}\n"
                f"Disclaimer to include: {disclaimer}\n\n"
                f"Keep under 150 words. Professional but friendly tone."
            ),
        )
        return response.get("content", "Thank you for contacting us. We will be in touch shortly.")

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        patient_id: str,
    ) -> dict:
        """Send email via Resend."""
        try:
            result = await self.email_client.send(
                to=to,
                subject=subject,
                html=f"<p>{body}</p>",
            )

            write_audit_log(
                event_type="email_sent",
                clinic_id=self.clinic_id,
                patient_id=patient_id,
                agent_type=self.agent_type,
                metadata={"email_id": result.get("email_id"), "subject": subject[:50]},
            )

            return {
                "status": result.get("status", "sent"),
                "email_id": result.get("email_id"),
            }

        except Exception as e:
            logger.error("Email send failed to %s: %s", to[:10], str(e))
            return {"status": "failed", "error": str(e)}
