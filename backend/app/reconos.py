"""ReconOS OFE Bridge — clinic OSINT intelligence."""
from app.bridges.base_bridge import BaseBridge

class ReconOSBridge(BaseBridge):
    product_name = "ReconOS"

    async def fetch_clinic_intel(self, clinic_name: str,
                                  location: str = "") -> dict:
        try:
            result = await self._post("/intel/clinic", {
                "clinic_name": clinic_name, "location": location,
                "source": "carenova",
            })
            return {"sent": True, **result}
        except Exception as e:
            return self._safe_result(e)
