"""FadeReach Bridge — patient recall + clinic onboarding sequences."""
from app.bridges.base_bridge import BaseBridge

class FadeReachBridge(BaseBridge):
    product_name = "FadeReach"

    async def trigger_sequence(self, sequence_id: str, clinic_id: str,
                                contact_email: str, metadata: dict = None) -> dict:
        try:
            await self._post("/sequences/trigger", {
                "sequence_id": sequence_id, "clinic_id": clinic_id,
                "contact_email": contact_email, "metadata": metadata or {},
            })
            return {"sent": True}
        except Exception as e:
            return self._safe_result(e)

    async def trigger_recall_campaign(self, clinic_id: str,
                                       campaign_type: str, patient_count: int) -> dict:
        try:
            await self._post("/campaigns/recall", {
                "clinic_id": clinic_id, "campaign_type": campaign_type,
                "patient_count": patient_count,
            })
            return {"sent": True}
        except Exception as e:
            return self._safe_result(e)
