"""BugFlow Elite Bridge — security audit pipeline."""
from app.bridges.base_bridge import BaseBridge

class BugFlowBridge(BaseBridge):
    product_name = "BugFlow"

    async def trigger_scan(self, scan_type: str, target: str,
                            clinic_id: str = "") -> dict:
        try:
            result = await self._post("/scans/trigger", {
                "scan_type": scan_type, "target": target,
                "clinic_id": clinic_id, "source": "carenova",
            })
            return {"sent": True, "scan_id": result.get("scan_id")}
        except Exception as e:
            return self._safe_result(e)
