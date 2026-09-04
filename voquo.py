"""Voquo Bridge — AI video production for patient education."""
from app.bridges.base_bridge import BaseBridge

class VoquoBridge(BaseBridge):
    product_name = "Voquo"

    async def request_video(self, video_type: str, clinic_id: str,
                             topic: str, metadata: dict = None) -> dict:
        try:
            result = await self._post("/videos/generate", {
                "video_type": video_type, "clinic_id": clinic_id,
                "topic": topic, "metadata": metadata or {},
            })
            return {"sent": True, "job_id": result.get("job_id")}
        except Exception as e:
            return self._safe_result(e)
