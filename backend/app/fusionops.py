"""
FusionOps Bridge — routes all Carenova events to FusionOps hub.
EC2 Stockholm: 13.50.16.19:8080
Governing rule: all product-to-product communication goes through FusionOps.
Fire-and-forget async. Graceful fallback if FusionOps is down.
"""
import logging
import httpx

logger = logging.getLogger(__name__)


class FusionOpsBridge:
    """Routes Carenova events to FusionOps technical hub."""

    def __init__(self, url: str, api_key: str) -> None:
        self.url = url
        self.api_key = api_key

    async def send_event(
        self,
        event_type: str,
        clinic_id: str,
        payload: dict,
    ) -> dict:
        """Send event to FusionOps. Never raises — graceful fallback."""
        try:
            result = await self._post(
                "/events",
                {
                    "source": "carenova",
                    "event_type": event_type,
                    "clinic_id": clinic_id,
                    "payload": payload,
                },
            )
            return {"sent": True, "result": result}
        except Exception as e:
            logger.warning("FusionOps unavailable: %s — continuing", str(e))
            return {"sent": False, "error": str(e)}

    async def _post(self, path: str, data: dict) -> dict:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.post(
                f"{self.url}{path}",
                json=data,
                headers={"X-API-Key": self.api_key},
            )
            r.raise_for_status()
            return r.json()
