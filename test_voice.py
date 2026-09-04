"""
Retell AI Voice Layer Tests — Sprint 6
TDD RED phase.

Retell AI handles all voice calls at $0.07/min with HIPAA BAA.
This layer wraps Retell webhooks and the voice router.

Responsibilities:
  - Receive Retell webhook events (call_started, call_ended, transcript)
  - Verify webhook signatures for security
  - Route call events to correct agent
  - Handle call transfers to human staff
  - Store call recordings reference in Cloudflare R2
  - Validate webhook payload structure
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import hmac
import hashlib
import json


class TestRetellClientInitialisation:

    def test_retell_client_can_be_imported(self):
        from app.voice.retell_client import RetellClient
        assert RetellClient is not None

    def test_retell_client_requires_api_key(self):
        from app.voice.retell_client import RetellClient
        with pytest.raises(TypeError):
            RetellClient()

    def test_retell_client_stores_api_key(self):
        from app.voice.retell_client import RetellClient
        client = RetellClient(api_key="test_key_abc")
        assert client.api_key == "test_key_abc"


class TestRetellWebhookVerification:

    def test_valid_signature_passes_verification(self):
        """Valid HMAC-SHA256 signature passes."""
        from app.voice.retell_client import RetellClient

        secret = "webhook_secret_123"
        client = RetellClient(api_key="test_key", webhook_secret=secret)

        payload = b'{"event": "call_started", "call": {"call_id": "abc"}}'
        signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        assert client.verify_webhook_signature(payload, signature) is True

    def test_invalid_signature_fails_verification(self):
        """Tampered payload fails signature check."""
        from app.voice.retell_client import RetellClient

        client = RetellClient(api_key="test_key", webhook_secret="secret_abc")
        payload = b'{"event": "call_started"}'

        assert client.verify_webhook_signature(payload, "bad_signature") is False

    def test_missing_signature_fails_verification(self):
        """Empty signature fails."""
        from app.voice.retell_client import RetellClient

        client = RetellClient(api_key="test_key", webhook_secret="secret_abc")
        assert client.verify_webhook_signature(b"payload", "") is False


class TestRetellWebhookRouting:

    @pytest.mark.asyncio
    async def test_call_started_event_routes_to_handler(
        self, retell_call_started_payload
    ):
        """call_started event triggers handle_call_started."""
        from app.voice.retell_client import RetellClient

        client = RetellClient(api_key="test_key", webhook_secret="secret")
        mock_handler = AsyncMock(return_value={"greeting": "Hello!"})
        client.on_call_started = mock_handler

        result = await client.route_event(retell_call_started_payload)

        mock_handler.assert_called_once()
        assert result is not None

    @pytest.mark.asyncio
    async def test_call_ended_event_routes_to_handler(
        self, retell_call_ended_payload
    ):
        """call_ended event triggers handle_call_ended."""
        from app.voice.retell_client import RetellClient

        client = RetellClient(api_key="test_key", webhook_secret="secret")
        mock_handler = AsyncMock(return_value={"stored": True})
        client.on_call_ended = mock_handler

        result = await client.route_event(retell_call_ended_payload)

        mock_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_event_returns_acknowledged(self):
        """Unknown event type is acknowledged without error."""
        from app.voice.retell_client import RetellClient

        client = RetellClient(api_key="test_key", webhook_secret="secret")

        result = await client.route_event({"event": "unknown_future_event"})

        assert result["status"] == "acknowledged"

    @pytest.mark.asyncio
    async def test_call_started_extracts_clinic_id_from_metadata(
        self, retell_call_started_payload
    ):
        """clinic_id is extracted from call metadata for routing."""
        from app.voice.retell_client import RetellClient

        client = RetellClient(api_key="test_key", webhook_secret="secret")
        client.on_call_started = AsyncMock(return_value={})

        await client.route_event(retell_call_started_payload)

        call_kwargs = client.on_call_started.call_args[1]
        assert call_kwargs.get("clinic_id") == "clinic_test_001"


class TestRetellCallHandler:

    @pytest.mark.asyncio
    async def test_call_handler_creates_reception_agent(
        self, clinic_id, mock_llm_gateway, mock_graphiti, retell_call_started_payload
    ):
        """
        When a call starts, CallHandler creates a ReceptionAgent
        for the correct clinic.
        """
        from app.voice.call_handler import CallHandler

        handler = CallHandler()

        with patch("app.voice.call_handler.ReceptionAgent") as MockAgent:
            mock_agent = AsyncMock()
            mock_agent.handle_call_started = AsyncMock(
                return_value={"greeting": "Hello!", "call_id": "call_abc123"}
            )
            MockAgent.return_value = mock_agent

            result = await handler.handle_call_started(
                call_id="call_abc123",
                from_number="+12125551234",
                clinic_id=clinic_id,
            )

            MockAgent.assert_called_once()
            call_kwargs = MockAgent.call_args[1]
            assert call_kwargs["clinic_id"] == clinic_id
            assert result["greeting"] == "Hello!"
            assert result["greeting"] == "Hello!"

    @pytest.mark.asyncio
    async def test_call_handler_routes_ended_call_to_agent(
        self, clinic_id, retell_call_ended_payload
    ):
        """call_ended event reaches the correct agent."""
        from app.voice.call_handler import CallHandler

        handler = CallHandler()

        with patch("app.voice.call_handler.ReceptionAgent") as MockAgent:
            mock_agent = AsyncMock()
            mock_agent.handle_call_ended = AsyncMock(
                return_value={"episode_stored": True}
            )
            MockAgent.return_value = mock_agent

            result = await handler.handle_call_ended(
                call_data=retell_call_ended_payload["call"],
                clinic_id=clinic_id,
            )

            assert result["episode_stored"] is True


class TestRetellVoiceRouter:

    @pytest.mark.asyncio
    async def test_voice_router_webhook_returns_200(self):
        """Webhook endpoint returns 200 for valid Retell event."""
        from fastapi.testclient import TestClient
        from app.routers.voice import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        payload = {
            "event": "call_started",
            "call": {
                "call_id": "call_test_001",
                "call_type": "inbound",
                "from_number": "+12125551234",
                "to_number": "+18885550001",
                "metadata": {"clinic_id": "clinic_test_001"},
            },
        }

        with patch("app.routers.voice.call_handler") as mock_handler:
            mock_handler.handle_call_started = AsyncMock(
                return_value={"greeting": "Hello!", "call_id": "call_test_001"}
            )
            response = client.post(
                "/voice/webhook",
                json=payload,
                headers={"x-retell-signature": "skip_for_test"},
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_voice_router_returns_json_response(self):
        """Webhook endpoint returns JSON."""
        from fastapi.testclient import TestClient
        from app.routers.voice import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        payload = {
            "event": "call_ended",
            "call": {
                "call_id": "call_test_002",
                "call_type": "inbound",
                "from_number": "+12125551234",
                "to_number": "+18885550001",
                "duration_ms": 60000,
                "transcript": [],
                "metadata": {"clinic_id": "clinic_test_001"},
            },
        }

        with patch("app.routers.voice.call_handler") as mock_handler:
            mock_handler.handle_call_ended = AsyncMock(
                return_value={"episode_stored": True}
            )
            response = client.post(
                "/voice/webhook",
                json=payload,
                headers={"x-retell-signature": "skip_for_test"},
            )

        assert response.headers["content-type"].startswith("application/json")
