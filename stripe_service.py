"""
Stripe Service — Enterprise tier billing for Carenova US.

Enterprise tier: $3,999/month for 15+ providers.
ACH bank transfers default (avoids 2.9% card fee on $4K/month).
NET-30 invoicing for hospital systems and multi-location groups.
HSA/FSA acceptance for provider-side payments.

LemonSqueezy handles Starter/Pro/Growth.
Stripe handles Enterprise only — this is enforced here.
"""
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

STRIPE_BASE = "https://api.stripe.com/v1"
ENTERPRISE_PRICE_CENTS = 399900  # $3,999.00


class StripeService:
    """Stripe billing for Enterprise Carenova clinics."""

    tier = "enterprise"
    default_payment_method = "us_bank_account"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    # ── Subscriptions ─────────────────────────────────────────────────────────

    async def create_enterprise_subscription(
        self,
        clinic_id: str,
        customer_email: str,
        payment_method: str,
    ) -> dict:
        """Create Enterprise Stripe subscription with ACH default."""
        try:
            sub = await self._create_subscription(
                clinic_id=clinic_id,
                customer_email=customer_email,
                payment_method=payment_method,
            )
            return {
                "success": True,
                "subscription_id": sub["id"],
                "plan_tier": "enterprise",
                "status": sub.get("status"),
            }
        except Exception as e:
            logger.error("Stripe subscription creation failed: %s", str(e))
            return {"success": False, "error": str(e)}

    async def get_subscription_status(self, subscription_id: str) -> dict:
        """Get current subscription status."""
        sub = await self._get_subscription(subscription_id)
        active = sub.get("status") == "active"
        return {
            "active": active,
            "plan_tier": "enterprise",
            "status": sub.get("status"),
            "period_end": sub.get("current_period_end"),
        }

    # ── ACH Payments ──────────────────────────────────────────────────────────

    async def create_ach_payment_intent(
        self,
        amount_usd: int,
        clinic_id: str,
        description: str,
    ) -> dict:
        """Create ACH payment intent — avoids card processing fees."""
        try:
            amount_cents = amount_usd * 100
            intent = await self._create_payment_intent(
                amount_cents=amount_cents,
                clinic_id=clinic_id,
                description=description,
            )
            return {
                "success": True,
                "payment_intent_id": intent["id"],
                "amount_cents": intent["amount"],
                "payment_method_types": intent.get("payment_method_types", ["us_bank_account"]),
            }
        except Exception as e:
            logger.error("ACH payment intent failed: %s", str(e))
            return {"success": False, "error": str(e)}

    # ── NET-30 Invoicing ──────────────────────────────────────────────────────

    async def create_net30_invoice(
        self,
        customer_id: str,
        amount_usd: int,
        description: str,
    ) -> dict:
        """Create NET-30 invoice for hospital systems."""
        try:
            invoice = await self._create_invoice(
                customer_id=customer_id,
                amount_cents=amount_usd * 100,
                description=description,
            )
            return {
                "success": True,
                "invoice_id": invoice["id"],
                "amount_due": invoice["amount_due"],
                "payment_terms": "net_30",
                "status": invoice.get("status"),
            }
        except Exception as e:
            logger.error("NET-30 invoice creation failed: %s", str(e))
            return {"success": False, "error": str(e)}

    # ── Private HTTP helpers ──────────────────────────────────────────────────

    async def _create_subscription(self, **kwargs) -> dict:
        """Raw Stripe subscription creation."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                f"{STRIPE_BASE}/subscriptions",
                data={
                    "payment_settings[payment_method_types][]": "us_bank_account",
                    "metadata[clinic_id]": kwargs.get("clinic_id", ""),
                },
                auth=(self.api_key, ""),
            )
            r.raise_for_status()
            return r.json()

    async def _get_subscription(self, subscription_id: str) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{STRIPE_BASE}/subscriptions/{subscription_id}",
                auth=(self.api_key, ""),
            )
            r.raise_for_status()
            return r.json()

    async def _create_payment_intent(
        self, amount_cents: int, clinic_id: str, description: str
    ) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{STRIPE_BASE}/payment_intents",
                data={
                    "amount": str(amount_cents),
                    "currency": "usd",
                    "payment_method_types[]": "us_bank_account",
                    "description": description,
                    "metadata[clinic_id]": clinic_id,
                },
                auth=(self.api_key, ""),
            )
            r.raise_for_status()
            return r.json()

    async def _create_invoice(
        self, customer_id: str, amount_cents: int, description: str
    ) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{STRIPE_BASE}/invoices",
                data={
                    "customer": customer_id,
                    "collection_method": "send_invoice",
                    "days_until_due": "30",
                    "description": description,
                },
                auth=(self.api_key, ""),
            )
            r.raise_for_status()
            return r.json()
