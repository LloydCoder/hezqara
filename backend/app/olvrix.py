"""Olvrix Bridge — clinic lead prospecting events."""
from app.bridges.base_bridge import BaseBridge

class OlvrixBridge(BaseBridge):
    product_name = "Olvrix"

    async def fire_event(self, event_type: str, clinic_id: str, metadata: dict = None) -> dict:
        try:
            await self._post("/events", {
                "event_type": event_type, "clinic_id": clinic_id,
                "source": "carenova", "metadata": metadata or {},
            })
            return {"sent": True}
        except Exception as e:
            return self._safe_result(e)
