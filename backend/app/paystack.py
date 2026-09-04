"""
Paystack Service — billing for Nigeria clinics.
Amounts in kobo (NGN × 100).
"""
import logging
import httpx

logger = logging.getLogger(__name__)
PAYSTACK_BASE = "https://api.paystack.co"


class PaystackService:
    """Paystack billing for Carenova Nigeria."""

    def __init__(self, secret_key: str) -> None:
        self.secret_key = secret_key

    async def verify_payment(self, reference: str) -> dict:
        """Verify Paystack payment reference."""
        data = await self._verify_reference(reference)
        payment_data = data.get("data", {})
        success = (
            data.get("status") is True
            and payment_data.get("status") == "success"
        )
        amount_kobo = payment_data.get("amount", 0)

        return {
            "success": success,
            "reference": reference,
            "amount_ngn": amount_kobo // 100,
            "amount_kobo": amount_kobo,
        }

    async def _verify_reference(self, reference: str) -> dict:
        """Fetch raw verification from Paystack API."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{PAYSTACK_BASE}/transaction/verify/{reference}",
                headers={"Authorization": f"Bearer {self.secret_key}"},
            )
            r.raise_for_status()
            return r.json()
