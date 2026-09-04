"""
WhatsApp Business API Client — Nigeria channel.
Replaces Retell AI voice for Nigerian clinics.
Works on 2G — critical for Nigerian market.
"""
import json
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

WHATSAPP_BASE = "https://graph.facebook.com/v21.0"


class WhatsAppClient:
    """WhatsApp Business API for patient communication in Nigeria."""

    def __init__(
        self,
        api_token: str,
        phone_number_id: str,
        verify_token: str,
    ) -> None:
        self.api_token = api_token
        self.phone_number_id = phone_number_id
        self.verify_token = verify_token

    async def send_text(self, to: str, message: str) -> dict:
        """Send plain text WhatsApp message."""
        try:
            result = await self._post(
                f"/{self.phone_number_id}/messages",
                {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to.replace("+", ""),
                    "type": "text",
                    "text": {"preview_url": False, "body": message},
                },
            )
            messages = result.get("messages", [])
            message_id = messages[0]["id"] if messages else None
            return {"success": True, "message_id": message_id}

        except Exception as e:
            logger.error("WhatsApp send_text failed: %s", str(e))
            return {"success": False, "error": str(e)}

    async def send_template(
        self,
        to: str,
        template_name: str,
        language: str,
        components: list,
    ) -> dict:
        """Send WhatsApp template message (pre-approved by Meta)."""
        try:
            result = await self._post(
                f"/{self.phone_number_id}/messages",
                {
                    "messaging_product": "whatsapp",
                    "to": to.replace("+", ""),
                    "type": "template",
                    "template": {
                        "name": template_name,
                        "language": {"code": language},
                        "components": components,
                    },
                },
            )
            messages = result.get("messages", [])
            return {"success": True, "message_id": messages[0]["id"] if messages else None}

        except Exception as e:
            logger.error("WhatsApp template send failed: %s", str(e))
            return {"success": False, "error": str(e)}

    def verify_webhook(
        self,
        mode: str,
        challenge: str,
        token: str,
    ) -> Optional[str]:
        """Verify WhatsApp webhook registration challenge."""
        if mode == "subscribe" and token == self.verify_token:
            return challenge
        return None

    def parse_inbound_message(self, payload: dict) -> Optional[dict]:
        """Extract message from WhatsApp webhook payload."""
        try:
            entry = payload.get("entry", [{}])[0]
            change = entry.get("changes", [{}])[0]
            value = change.get("value", {})
            messages = value.get("messages", [])

            if not messages:
                return None

            msg = messages[0]
            return {
                "from": msg.get("from"),
                "message_id": msg.get("id"),
                "text": msg.get("text", {}).get("body", ""),
                "type": msg.get("type"),
                "timestamp": msg.get("timestamp"),
            }
        except (IndexError, KeyError) as e:
            logger.warning("Failed to parse WhatsApp payload: %s", str(e))
            return None

    async def _post(self, path: str, data: dict) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{WHATSAPP_BASE}{path}",
                json=data,
                headers={"Authorization": f"Bearer {self.api_token}"},
            )
            r.raise_for_status()
            return r.json()
