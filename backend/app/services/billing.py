"""
Billing Service — LemonSqueezy for US clinics.
Store ID: 247127 (Tinlance LemonSqueezy store).

Plan tiers:
  Starter    $499/month  — 1-2 providers
  Pro        $999/month  — 3-5 providers
  Growth     $1,999/month — 6-15 providers
  Enterprise $3,999/month — 15+ providers
"""
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

LEMONSQUEEZY_BASE = "https://api.lemonsqueezy.com/v1"

VARIANT_TIER_MAP = {
    "starter": "starter",
    "pro": "pro",
    "growth": "growth",
    "enterprise": "enterprise",
}


class BillingService:
    """LemonSqueezy billing for Carenova US clinics."""

    def __init__(self, api_key: str, store_id: str) -> None:
        self.api_key = api_key
        self.store_id = store_id

    def variant_to_tier(self, variant_name: str) -> str:
        """Map LemonSqueezy variant name to internal plan tier."""
        return VARIANT_TIER_MAP.get(variant_name.lower(), "starter")

    async def get_clinic_subscription(self, subscription_id: str) -> dict:
        """Fetch subscription status and map to plan tier."""
        sub = await self._get_subscription(subscription_id)
        active = sub.get("status") == "active"
        tier = self.variant_to_tier(sub.get("variant_name", "Starter"))

        return {
            "active": active,
            "plan_tier": tier,
            "status": sub.get("status"),
            "variant_name": sub.get("variant_name"),
        }

    async def _get_subscription(self, subscription_id: str) -> dict:
        """Fetch raw subscription from LemonSqueezy API."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{LEMONSQUEEZY_BASE}/subscriptions/{subscription_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            r.raise_for_status()
            data = r.json()
            attrs = data.get("data", {}).get("attributes", {})
            return {
                "status": attrs.get("status"),
                "variant_id": str(attrs.get("variant_id", "")),
                "variant_name": attrs.get("variant_name", "Starter"),
            }
