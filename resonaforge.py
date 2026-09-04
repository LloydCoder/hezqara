"""ResonaForge Bridge — brand authority intelligence."""
from app.bridges.base_bridge import BaseBridge

class ResonaForgeBridge(BaseBridge):
    product_name = "ResonaForge"

    async def send_brand_signal(self, signal_type: str, clinic_id: str,
                                 metadata: dict = None) -> dict:
        try:
            await self._post("/signals", {
                "signal_type": signal_type, "clinic_id": clinic_id,
                "source": "carenova", "metadata": metadata or {},
            })
            return {"sent": True}
        except Exception as e:
            return self._safe_result(e)
