"""
Nigeria WhatsApp Layer + NDPR Tests — Sprint 23
TDD RED phase.

Nigeria is Wave 2 market:
  - 39,914 clinics
  - WhatsApp-first (works on 2G)
  - NDPR compliance (not HIPAA)
  - Paystack/Flutterwave billing
  - Helium Health EHR
  - ₦50K–₦500K/month pricing

WhatsApp Business API replaces Retell AI voice for Nigeria.
NDPR replaces HIPAA for data governance.
Same 9 agents — different channel layer.
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestWhatsAppClientInitialisation:

    def test_whatsapp_client_can_be_imported(self):
        from app.voice.whatsapp import WhatsAppClient
        assert WhatsAppClient is not None

    def test_whatsapp_client_requires_credentials(self):
        from app.voice.whatsapp import WhatsAppClient
        with pytest.raises(TypeError):
            WhatsAppClient()

    def test_whatsapp_client_stores_phone_number_id(self):
        from app.voice.whatsapp import WhatsAppClient
        client = WhatsAppClient(
            api_token="token_abc",
            phone_number_id="123456789",
            verify_token="verify_abc",
        )
        assert client.phone_number_id == "123456789"


class TestWhatsAppMessageSending:

    @pytest.mark.asyncio
    async def test_send_text_message_to_patient(self):
        """Send WhatsApp text message to patient phone."""
        from app.voice.whatsapp import WhatsAppClient

        client = WhatsAppClient(
            api_token="token_abc",
            phone_number_id="123456789",
            verify_token="verify_abc",
        )

        with patch.object(client, "_post", return_value={
            "messages": [{"id": "wamid.001"}]
        }):
            result = await client.send_text(
                to="+2348012345678",
                message="Ndewo! Family Care Clinic na-akpọ ọnụ. Kedu ka ọ dị?",
            )

        assert result["success"] is True
        assert result["message_id"] == "wamid.001"

    @pytest.mark.asyncio
    async def test_send_appointment_template_message(self):
        """Send WhatsApp template message for appointment confirmation."""
        from app.voice.whatsapp import WhatsAppClient

        client = WhatsAppClient(
            api_token="token_abc",
            phone_number_id="123456789",
            verify_token="verify_abc",
        )

        with patch.object(client, "_post", return_value={
            "messages": [{"id": "wamid.002"}]
        }):
            result = await client.send_template(
                to="+2348012345678",
                template_name="appointment_confirmation",
                language="en",
                components=[
                    {"type": "body", "parameters": [
                        {"type": "text", "text": "Dr. Okonkwo"},
                        {"type": "text", "text": "Tuesday July 1st at 10 AM"},
                    ]}
                ],
            )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_message_failure_returns_error(self):
        """WhatsApp API failure returns error — never crashes."""
        from app.voice.whatsapp import WhatsAppClient

        client = WhatsAppClient(
            api_token="token_abc",
            phone_number_id="123456789",
            verify_token="verify_abc",
        )

        with patch.object(client, "_post", side_effect=Exception("WhatsApp API error")):
            result = await client.send_text(
                to="+2348012345678",
                message="Test message",
            )

        assert result["success"] is False
        assert "error" in result


class TestWhatsAppWebhookHandling:

    def test_verify_webhook_challenge(self):
        """WhatsApp webhook verification challenge response."""
        from app.voice.whatsapp import WhatsAppClient

        client = WhatsAppClient(
            api_token="token_abc",
            phone_number_id="123456789",
            verify_token="my_verify_token",
        )

        result = client.verify_webhook(
            mode="subscribe",
            challenge="challenge_12345",
            token="my_verify_token",
        )

        assert result == "challenge_12345"

    def test_invalid_verify_token_rejected(self):
        """Wrong verify token is rejected."""
        from app.voice.whatsapp import WhatsAppClient

        client = WhatsAppClient(
            api_token="token_abc",
            phone_number_id="123456789",
            verify_token="correct_token",
        )

        result = client.verify_webhook(
            mode="subscribe",
            challenge="challenge_12345",
            token="wrong_token",
        )

        assert result is None

    def test_parse_inbound_message(self):
        """Parse incoming WhatsApp message payload."""
        from app.voice.whatsapp import WhatsAppClient

        client = WhatsAppClient(
            api_token="token_abc",
            phone_number_id="123456789",
            verify_token="verify_abc",
        )

        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "2348012345678",
                            "id": "wamid.inbound_001",
                            "text": {"body": "I want to book appointment"},
                            "type": "text",
                            "timestamp": "1751328000",
                        }]
                    }
                }]
            }]
        }

        message = client.parse_inbound_message(payload)

        assert message is not None
        assert message["from"] == "2348012345678"
        assert message["text"] == "I want to book appointment"
        assert message["message_id"] == "wamid.inbound_001"


class TestNDPACompliance:
    """
    NDPA + GAID — Nigeria Data Protection Act, 2023.
    Replaces the obsolete NDPR 2019, which ceased to apply once the
    GAID took effect on 19 September 2025.
    """

    def test_ndpa_module_can_be_imported(self):
        from app.compliance.ndpa import NDPACompliance
        assert NDPACompliance is not None

    def test_ndpa_data_subject_rights(self):
        """NDPA grants patients right to access their data."""
        from app.compliance.ndpa import NDPACompliance

        rights = NDPACompliance.get_data_subject_rights()

        assert "access" in rights
        assert "erasure" in rights
        assert "portability" in rights
        assert "object_to_automated_processing" in rights

    def test_ndpa_act_info_correct(self):
        """NDPA replaced NDPR — terminology must be accurate."""
        from app.compliance.ndpa import NDPACompliance

        info = NDPACompliance.get_act_info()
        assert info["act_name"] == "Nigeria Data Protection Act, 2023"
        assert info["regulator"] == "Nigeria Data Protection Commission (NDPC)"

    def test_ndpa_data_localization_via_cross_border_module(self):
        """Cross-border transfer assessment — Supabase Frankfurt is EU adequacy."""
        from app.compliance.ndpa import CrossBorderTransfer

        assert CrossBorderTransfer.is_adequate_jurisdiction("EU/Frankfurt") is True
        assert CrossBorderTransfer.is_adequate_jurisdiction("US/us-east-1") is False

    def test_ndpa_breach_notification_72_hours(self):
        """NDPA requires breach notification within 72 hours."""
        from app.compliance.ndpa import NDPACompliance

        info = NDPACompliance.get_act_info()
        assert info["breach_notification_hours"] == 72

    def test_deprecated_ndpr_shim_still_importable(self):
        """Old code that imports app.compliance.ndpr must not crash."""
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from app.compliance.ndpr import NDPRCompliance
            assert NDPRCompliance is not None
            assert any(issubclass(x.category, DeprecationWarning) for x in w)


class TestHeliumHealthEHR:
    """Helium Health — Nigeria's leading EHR system."""

    def test_helium_health_client_can_be_imported(self):
        from app.ehr.helium_health import HeliumHealthClient
        assert HeliumHealthClient is not None

    def test_helium_health_implements_base_ehr(self):
        from app.ehr.helium_health import HeliumHealthClient
        from app.ehr.base import BaseEHR
        assert issubclass(HeliumHealthClient, BaseEHR)

    def test_helium_health_requires_credentials(self):
        from app.ehr.helium_health import HeliumHealthClient
        with pytest.raises(TypeError):
            HeliumHealthClient()

    def test_helium_health_stores_facility_id(self):
        from app.ehr.helium_health import HeliumHealthClient
        client = HeliumHealthClient(
            api_key="hh_test_key",
            facility_id="FAC_LAGOS_001",
        )
        assert client.facility_id == "FAC_LAGOS_001"

    @pytest.mark.asyncio
    async def test_helium_health_get_patient_by_phone(self):
        from app.ehr.helium_health import HeliumHealthClient

        client = HeliumHealthClient(
            api_key="hh_test_key",
            facility_id="FAC_LAGOS_001",
        )

        with patch.object(client, "_get", return_value={
            "data": [{
                "id": "PAT_NG_001",
                "first_name": "Chidi",
                "last_name": "Okeke",
                "phone": "08012345678",
            }]
        }):
            result = await client.get_patient(
                clinic_id="clinic_ng_001",
                phone="+2348012345678",
            )

        assert result is not None
        assert result["patient_id"] == "PAT_NG_001"

    @pytest.mark.asyncio
    async def test_helium_health_book_appointment_writeback(self):
        """Appointment write-back to Helium Health EHR."""
        from app.ehr.helium_health import HeliumHealthClient

        client = HeliumHealthClient(
            api_key="hh_test_key",
            facility_id="FAC_LAGOS_001",
        )

        with patch.object(client, "_post", return_value={
            "data": {"id": "APT_NG_001", "start_time": "2026-07-01T10:00:00"},
        }):
            result = await client.book_appointment(
                clinic_id="clinic_ng_001",
                patient_id="PAT_NG_001",
                slot_id="SLOT_001",
                reason="General consultation",
            )

        assert result["appointment_id"] == "APT_NG_001"
        assert result["status"] == "confirmed"


class TestNigeriaGeoPricing:
    """Nigeria geo-pricing — ₦50K–₦500K/month."""

    def test_geo_pricing_module_can_be_imported(self):
        from app.services.geo_pricing import GeoPricingService
        assert GeoPricingService is not None

    def test_nigeria_pricing_is_correct(self):
        from app.services.geo_pricing import GeoPricingService

        svc = GeoPricingService()
        pricing = svc.get_pricing(country="NG", tier="starter")

        assert pricing["currency"] == "NGN"
        assert pricing["amount_ngn"] >= 50000
        assert pricing["amount_ngn"] <= 100000

    def test_us_pricing_uses_usd(self):
        from app.services.geo_pricing import GeoPricingService

        svc = GeoPricingService()
        pricing = svc.get_pricing(country="US", tier="starter")

        assert pricing["currency"] == "USD"
        assert pricing["amount_usd"] == 499

    def test_nigeria_multiplier_applied(self):
        """Nigeria pricing is 0.30x of US price (purchasing power parity)."""
        from app.services.geo_pricing import GeoPricingService

        svc = GeoPricingService()
        us = svc.get_pricing(country="US", tier="pro")
        ng = svc.get_pricing(country="NG", tier="pro")

        # Nigeria should be significantly cheaper in USD terms
        assert ng["amount_usd_equivalent"] < us["amount_usd"]

    def test_payment_provider_for_nigeria_is_paystack(self):
        from app.services.billing_router import select_payment_provider

        provider = select_payment_provider(tier="enterprise", country="NG")
        assert provider == "paystack"


class TestWhatsAppRouter:
    """WhatsApp webhook router — Nigeria channel."""

    def test_whatsapp_router_can_be_imported(self):
        from app.routers.whatsapp import router
        assert router is not None

    def test_whatsapp_webhook_verification_endpoint_exists(self):
        from app.routers.whatsapp import router
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.get(
            "/whatsapp/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "test_challenge",
                "hub.verify_token": "test_token",
            }
        )
        # Either 200 (valid token) or 403 (invalid) — not 404
        assert response.status_code != 404

    def test_whatsapp_inbound_message_endpoint_exists(self):
        from app.routers.whatsapp import router
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "2348012345678",
                            "id": "wamid.001",
                            "text": {"body": "Hello"},
                            "type": "text",
                            "timestamp": "1751328000",
                        }],
                        "metadata": {
                            "phone_number_id": "123456789",
                            "display_phone_number": "+2348099999999",
                        }
                    }
                }]
            }]
        }

        with patch("app.routers.whatsapp.handle_inbound_message") as mock:
            mock.return_value = {"processed": True}
            response = client.post("/whatsapp/webhook", json=payload)

        assert response.status_code == 200
