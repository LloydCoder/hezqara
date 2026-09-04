"""TwinGuard Bridge — agent containment + destructive action veto.
Fail-safe: timeout = approved (never block patient care).
"""
import httpx
from app.bridges.base_bridge import BaseBridge

class TwinGuardBridge(BaseBridge):
    product_name = "TwinGuard"

    async def validate_action(self, action_type: str, clinic_id: str,
                               payload: dict = None) -> dict:
        try:
            result = await self._post("/actions/validate", {
                "action_type": action_type, "clinic_id": clinic_id,
                "source": "carenova", "payload": payload or {},
            })
            return {
                "approved": result.get("approved", True),
                "veto": result.get("veto", False),
                "confidence": result.get("confidence", 1.0),
                "reason": result.get("reason"),
            }
        except (httpx.TimeoutException, httpx.ConnectError):
            # Fail-safe: timeout = approved — never block patient care
            return {"approved": True, "veto": False, "fallback": True}
        except Exception as e:
            return {"approved": True, "veto": False, **self._safe_result(e)}
