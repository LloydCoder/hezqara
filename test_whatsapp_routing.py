"""
Tests for WhatsApp webhook → Walk-in intake routing.
Fixes the gap where handle_inbound_message() was a stub doing nothing.

Also covers: clinic lookup by WhatsApp phone_number_id, and the
WhatsApp utility template service needed for messages sent outside
the 24-hour free service window (queue-called notifications, follow-up
reminders).
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestWhatsAppToWalkInRouting:

    @pytest.mark.asyncio
    async def test_inbound_message_routes_to_walkin_handler(self):
        """
        Patient sends WhatsApp message → must reach WalkInIntakeHandler,
        not just log and return. This was the confirmed gap.
        """
        from app.routers.whatsapp import handle_inbound_message

        message = {
            "from": "+2348031234567",
            "text": "Amaka Obi, fever and headache",
            "message_id": "wamid.123",
        }

        with patch(
            "app.routers.whatsapp.WalkInIntakeHandler.handle_message",
            new_callable=AsyncMock,
            return_value={
                "action": "registered",
                "reply": "You are #3, wait ~30 min",
                "queue_number": 3,
            },
        ) as mock_handle:
            result = await handle_inbound_message(message, clinic_id="clinic_ng_001")

        mock_handle.assert_called_once()
        assert result["processed"] is True
        assert result.get("queue_number") == 3

    @pytest.mark.asyncio
    async def test_inbound_message_sends_reply_via_whatsapp(self):
        """The handler's reply text must actually be sent back to the patient."""
        from app.routers.whatsapp import handle_inbound_message

        message = {"from": "+2348031234567", "text": "Hi", "message_id": "wamid.456"}

        sent_replies = []

        with patch(
            "app.routers.whatsapp.WalkInIntakeHandler.handle_message",
            new_callable=AsyncMock,
            return_value={"action": "greet", "reply": "Welcome! What is your name?"},
        ):
            with patch(
                "app.routers.whatsapp._send_reply",
                new_callable=AsyncMock,
                side_effect=lambda phone, text: sent_replies.append((phone, text)),
            ):
                await handle_inbound_message(message, clinic_id="clinic_ng_001")

        assert len(sent_replies) == 1
        assert sent_replies[0][0] == "+2348031234567"
        assert "Welcome" in sent_replies[0][1]

    @pytest.mark.asyncio
    async def test_clinic_lookup_by_phone_number_id(self):
        """
        Production gap: clinic_id was hardcoded to 'clinic_ng_default'.
        Must look up the actual clinic from the WhatsApp phone_number_id
        in the webhook payload.
        """
        from app.routers.whatsapp import resolve_clinic_id

        with patch(
            "app.routers.whatsapp._lookup_clinic_by_whatsapp_number",
            new_callable=AsyncMock,
            return_value="clinic_ng_owerri_001",
        ):
            clinic_id = await resolve_clinic_id(phone_number_id="108234567890123")

        assert clinic_id == "clinic_ng_owerri_001"

    @pytest.mark.asyncio
    async def test_clinic_lookup_falls_back_to_default_if_unmapped(self):
        from app.routers.whatsapp import resolve_clinic_id

        with patch(
            "app.routers.whatsapp._lookup_clinic_by_whatsapp_number",
            new_callable=AsyncMock,
            return_value=None,
        ):
            clinic_id = await resolve_clinic_id(phone_number_id="unknown_number_id")

        assert clinic_id is not None  # Should not crash, falls back gracefully


class TestWhatsAppUtilityTemplates:
    """
    Messages sent outside the 24h free service window (queue-called
    notifications sent later, follow-up reminders) require Meta-approved
    utility templates, not free-form text. Fixes confirmed gap #4.
    """

    def test_template_service_importable(self):
        from app.services.whatsapp_templates import WhatsAppTemplateService
        assert WhatsAppTemplateService is not None

    def test_register_utility_template(self):
        from app.services.whatsapp_templates import WhatsAppTemplateService
        svc = WhatsAppTemplateService()
        template = svc.register_template(
            template_name="queue_called_v1",
            language="en",
            category="utility",
            body_text="It's your turn! Please come to {{1}} now.",
        )
        assert template["category"] == "utility"
        assert template["approval_status"] == "pending"

    def test_follow_up_reminder_uses_utility_category(self):
        """Follow-up reminders must be utility, not marketing — for cost and deliverability."""
        from app.services.whatsapp_templates import WhatsAppTemplateService
        svc = WhatsAppTemplateService()
        template = svc.get_template_for("followup_reminder", language="en")
        assert template["category"] == "utility"

    def test_queue_called_uses_utility_category(self):
        from app.services.whatsapp_templates import WhatsAppTemplateService
        svc = WhatsAppTemplateService()
        template = svc.get_template_for("queue_called", language="en")
        assert template["category"] == "utility"

    def test_send_within_service_window_uses_free_form(self):
        """If patient messaged within last 24h, use free-form text — no template needed."""
        from app.services.whatsapp_templates import WhatsAppTemplateService
        svc = WhatsAppTemplateService()
        decision = svc.decide_message_type(
            last_patient_message_hours_ago=2,
            message_purpose="queue_called",
        )
        assert decision["use_template"] is False
        assert decision["reason"] == "within_24h_service_window"

    def test_send_outside_service_window_requires_template(self):
        from app.services.whatsapp_templates import WhatsAppTemplateService
        svc = WhatsAppTemplateService()
        decision = svc.decide_message_type(
            last_patient_message_hours_ago=72,
            message_purpose="followup_reminder",
        )
        assert decision["use_template"] is True
        assert decision["template_category"] == "utility"

    def test_all_walkin_templates_pre_registered(self):
        """The 10-language welcome/queue/called/followup templates must all be registered."""
        from app.services.whatsapp_templates import WhatsAppTemplateService
        svc = WhatsAppTemplateService()
        templates = svc.get_all_templates()
        names = {t["template_name"] for t in templates}
        assert "queue_called" in names
        assert "followup_reminder" in names
