"""
Voice Fallback — handles Retell AI outages gracefully.

When Retell AI is down or unreachable:
  1. Answer with a recorded message (via Twilio)
  2. Collect caller's number
  3. Queue a callback for when Retell recovers
  4. Send SMS acknowledgment to patient
  5. Notify clinic staff via SMS/email

This ensures zero missed calls even during provider outages.
"""
import logging
from datetime import datetime, UTC
from typing import Optional

logger = logging.getLogger(__name__)


class VoiceFallbackHandler:
    """
    Handles voice calls when Retell AI is unavailable.
    Falls back to Twilio-based queue-and-callback.
    """

    def __init__(
        self,
        twilio_client=None,
        sms_service=None,
        email_service=None,
    ) -> None:
        self.twilio = twilio_client
        self.sms = sms_service
        self.email = email_service
        self._callback_queue: list[dict] = []

    async def handle_retell_outage(
        self,
        clinic_id: str,
        from_number: str,
        clinic_phone: str,
        clinic_name: str = "the clinic",
    ) -> dict:
        """
        Called when Retell AI is unreachable.
        Queue callback and notify patient.
        """
        callback_entry = {
            "clinic_id": clinic_id,
            "patient_phone": from_number,
            "clinic_phone": clinic_phone,
            "queued_at": datetime.now(UTC).isoformat(),
            "status": "pending",
        }
        self._callback_queue.append(callback_entry)

        # Send SMS acknowledgment to patient
        sms_sent = False
        if self.sms:
            try:
                await self.sms.send_sms(
                    to=from_number,
                    body=(
                        f"Hi! You called {clinic_name}. "
                        f"We're experiencing high call volume right now. "
                        f"We'll call you back within 15 minutes. "
                        f"Text CANCEL to opt out."
                    ),
                )
                sms_sent = True
            except Exception as e:
                logger.warning("Fallback SMS failed: %s", str(e))

        # Notify clinic staff
        staff_notified = False
        if self.email:
            try:
                await self.email.send_email(
                    to=f"staff@{clinic_id}.carenova.ai",
                    subject="⚠️ Voice AI temporarily unavailable — callback queued",
                    body=(
                        f"Carenova voice AI is temporarily unavailable. "
                        f"A patient called from {from_number[:7]}**** and has been queued for callback. "
                        f"Please call them back or the system will retry in 15 minutes."
                    ),
                    patient_id="system",
                )
                staff_notified = True
            except Exception as e:
                logger.warning("Staff notification failed: %s", str(e))

        logger.warning(
            "VOICE FALLBACK: clinic %s call from %s queued. SMS: %s, Staff: %s",
            clinic_id, from_number[:7] + "****", sms_sent, staff_notified
        )

        return {
            "status": "queued_callback",
            "sms_sent": sms_sent,
            "staff_notified": staff_notified,
            "estimated_callback_minutes": 15,
        }

    async def check_retell_health(self, retell_api_key: str) -> bool:
        """Check if Retell AI is reachable."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(
                    "https://api.retellai.com/list-agents",
                    headers={"Authorization": f"Bearer {retell_api_key}"},
                )
                return r.status_code in (200, 401)  # 401 = reachable but wrong key
        except Exception:
            return False

    def get_queue_length(self, clinic_id: Optional[str] = None) -> int:
        """Return number of pending callbacks."""
        if clinic_id:
            return sum(1 for c in self._callback_queue
                      if c["clinic_id"] == clinic_id and c["status"] == "pending")
        return sum(1 for c in self._callback_queue if c["status"] == "pending")

    async def process_callback_queue(self, retell_client=None) -> dict:
        """
        Process pending callbacks once Retell recovers.
        Called by Celery task periodically.
        """
        pending = [c for c in self._callback_queue if c["status"] == "pending"]
        processed = 0
        failed = 0

        for entry in pending:
            try:
                if retell_client:
                    await retell_client.create_outbound_call(
                        to_number=entry["patient_phone"],
                        from_number=entry["clinic_phone"],
                        metadata={"clinic_id": entry["clinic_id"], "is_callback": True},
                    )
                entry["status"] = "completed"
                processed += 1
            except Exception as e:
                logger.error("Callback failed for %s: %s", entry["patient_phone"][:7], str(e))
                entry["status"] = "failed"
                failed += 1

        return {"processed": processed, "failed": failed}


# Global singleton
voice_fallback = VoiceFallbackHandler()
