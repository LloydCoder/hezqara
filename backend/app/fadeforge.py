"""fadeforge Bridge — Tinlance ecosystem integration."""
from app.bridges.base_bridge import BaseBridge
import logging
logger = logging.getLogger(__name__)

class FadeforgeBridge(BaseBridge):
    product_name = "fadeforge"

    async def send_event(self, event_type: str, clinic_id: str,
                          payload: dict = None) -> dict:
        try:
            await self._post("/events", {
                "event_type": event_type, "clinic_id": clinic_id,
                "source": "carenova", "payload": payload or {},
            })
            return {"sent": True}
        except Exception as e:
            return self._safe_result(e)
