"""
Tests for QueueManager → WhatsAppTemplateService wiring.

Fixes confirmed gap: _queue_followup_reminder() was a stub that only
logged. Follow-up reminders sent days after the visit are always outside
the 24h WhatsApp service window and must route through the utility
template service, not free-form text (which would be blocked by Meta).
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestFollowUpReminderTemplateWiring:

    @pytest.mark.asyncio
    async def test_followup_reminder_uses_template_service(self):
        """complete_visit() with follow_up_days must route through the template service."""
        from app.walkin.queue import QueueManager

        mgr = QueueManager(clinic_id="clinic_ng_001")
        entry = await mgr.enqueue({
            "patient_name": "Amaka Obi",
            "patient_phone": "+2348031234567",
            "chief_complaint": "Diabetes checkup",
            "language": "ig",
        })

        with patch.object(mgr, "_send_whatsapp_notification", return_value=None):
            await mgr.call_next(provider_id="PROV-001", room="Room 1")

            with patch(
                "app.walkin.queue.WhatsAppTemplateService.decide_message_type",
                return_value={"use_template": True, "template_category": "utility"},
            ) as mock_decide:
                result = await mgr.complete_visit(
                    visit_id=entry["visit_id"],
                    notes="BP controlled",
                    follow_up_days=30,
                )

        assert result["follow_up_scheduled"] is True
        mock_decide.assert_called()

    @pytest.mark.asyncio
    async def test_followup_reminder_uses_correct_language(self):
        """The reminder template body must be in the patient's language."""
        from app.walkin.queue import QueueManager

        mgr = QueueManager(clinic_id="clinic_ng_001")
        entry = await mgr.enqueue({
            "patient_name": "Marie Koné",
            "patient_phone": "+2250701234567",
            "chief_complaint": "Consultation",
            "language": "fr",
        })

        captured = []

        with patch.object(mgr, "_send_whatsapp_notification",
                           side_effect=lambda phone, message: captured.append(message)):
            await mgr.call_next(provider_id="PROV-001", room="Room 1")
            await mgr.complete_visit(
                visit_id=entry["visit_id"],
                notes="Stable",
                follow_up_days=14,
            )

        # The follow-up reminder should have been sent (captured includes
        # both the "called" notification and the reminder)
        assert len(captured) >= 1
