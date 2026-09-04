"""
Retell AI Client — voice call wrapper for Carenova.
HIPAA BAA signed. $0.07/min. 600ms latency.
"""
import hmac
import hashlib
import logging
from typing import Optional, Any, Callable

logger = logging.getLogger(__name__)


class RetellClient:
    """Wraps Retell AI SDK for Carenova voice calls."""

    def __init__(
        self,
        api_key: str,
        webhook_secret: Optional[str] = None,
        base_url: str = "https://api.retellai.com",
    ) -> None:
        self.api_key = api_key
        self.webhook_secret = webhook_secret or ""
        self.base_url = base_url
        self.on_call_started: Optional[Callable] = None
        self.on_call_ended: Optional[Callable] = None
        self.on_transcript: Optional[Callable] = None

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """Verify Retell HMAC-SHA256 webhook signature."""
        if not signature:
            return False
        if not self.webhook_secret:
            return False

        expected = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    async def route_event(self, event: dict) -> dict:
        """Route Retell webhook event to correct handler."""
        event_type = event.get("event", "")
        call = event.get("call", {})
        metadata = call.get("metadata", {})
        clinic_id = metadata.get("clinic_id")

        if event_type == "call_started" and self.on_call_started:
            return await self.on_call_started(
                call_id=call.get("call_id"),
                from_number=call.get("from_number"),
                clinic_id=clinic_id,
            )

        if event_type == "call_ended" and self.on_call_ended:
            return await self.on_call_ended(
                call_data=call,
                clinic_id=clinic_id,
            )

        if event_type == "transcript" and self.on_transcript:
            return await self.on_transcript(
                call_id=event.get("call_id"),
                transcript=event.get("transcript", []),
                clinic_id=clinic_id,
            )

        logger.info("Unhandled Retell event type: %s", event_type)
        return {"status": "acknowledged", "event": event_type}
