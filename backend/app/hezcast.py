"""HezCast Bridge — patient communication content engine."""
from app.bridges.base_bridge import BaseBridge

class HezCastBridge(BaseBridge):
    product_name = "HezCast"

    async def generate_content(self, content_type: str, clinic_id: str,
                                variables: dict) -> dict:
        try:
            result = await self._post("/content/generate", {
                "content_type": content_type, "clinic_id": clinic_id,
                "variables": variables,
            })
            return {"sent": True, "content": result.get("content"), "content_id": result.get("content_id")}
        except Exception as e:
            return self._safe_result(e)
