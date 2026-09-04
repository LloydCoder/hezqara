"""
Ecosystem Bus — master event bus for all Tinlance product communication.
Routes Carenova events to FusionOps (and other bridges as needed).
Always fire-and-forget. Never raises. Never blocks patient care.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class EcosystemBus:
    """
    Central event bus for Carenova → Tinlance ecosystem.
    All events route through FusionOps per ecosystem governing rule.
    """

    def __init__(
        self,
        fusionops_url: str = "http://13.50.16.19:8080",
        fusionops_api_key: str = "",
    ) -> None:
        self.fusionops_url = fusionops_url
        self.fusionops_api_key = fusionops_api_key

    async def fire(
        self,
        event_type: str,
        clinic_id: str,
        payload: dict,
    ) -> None:
        """
        Fire event to ecosystem. Never raises.
        Patient care must never be blocked by telemetry failure.
        """
        try:
            await self._send_to_fusionops(
                event_type=event_type,
                clinic_id=clinic_id,
                payload=payload,
            )
        except Exception as e:
            logger.warning(
                "Ecosystem bus fire failed for event %s: %s — swallowing error",
                event_type, str(e)
            )

    async def _send_to_fusionops(
        self,
        event_type: str,
        clinic_id: str,
        payload: dict,
    ) -> dict:
        """Internal: send to FusionOps hub."""
        from app.bridges.fusionops import FusionOpsBridge

        bridge = FusionOpsBridge(
            url=self.fusionops_url,
            api_key=self.fusionops_api_key,
        )
        return await bridge.send_event(
            event_type=event_type,
            clinic_id=clinic_id,
            payload=payload,
        )
