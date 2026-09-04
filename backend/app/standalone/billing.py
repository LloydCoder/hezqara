"""
Patient Bill Collection — Nigeria payment rails.

Distinct from app/services/checkout.py (Carenova's own SaaS billing).
This handles PATIENT payments to the CLINIC — confirmed gap from market
research: Nigerian HMS must integrate with local payment gateways
(Paystack, Flutterwave, bank transfers) for both online and POS
payments. Only Paystack existed for this purpose before this build.

Payment methods by region:
  Nigeria: cash, pos, bank_transfer, paystack, flutterwave
  US:      card, insurance (existing US billing flow handles this)
"""
import uuid
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

NIGERIA_PAYMENT_METHODS = [
    {"id": "cash",          "label": "Cash",            "online": False},
    {"id": "pos",            "label": "POS Terminal",    "online": False},
    {"id": "bank_transfer",  "label": "Bank Transfer",    "online": False},
    {"id": "paystack",       "label": "Paystack",         "online": True},
    {"id": "flutterwave",    "label": "Flutterwave",      "online": True},
]

US_PAYMENT_METHODS = [
    {"id": "card",       "label": "Credit/Debit Card", "online": True},
    {"id": "insurance",  "label": "Insurance",          "online": False},
]

DEFAULT_PAYMENT_METHODS = US_PAYMENT_METHODS

VALID_OFFLINE_METHODS = {"cash", "pos", "bank_transfer"}


class PatientBillingService:
    """
    Patient bill collection for clinic visits — separate from the
    clinic's own Carenova subscription billing.
    """

    def __init__(self, clinic_id: str, country: str = "US") -> None:
        self.clinic_id = clinic_id
        self.country = country.upper()

    def get_available_payment_methods(self) -> list:
        """Region-appropriate payment methods for collecting from patients."""
        if self.country == "NG":
            return NIGERIA_PAYMENT_METHODS
        return DEFAULT_PAYMENT_METHODS

    async def create_payment_link(
        self,
        provider: str,
        amount_ngn: float,
        patient_name: str,
        patient_phone: str,
        description: str,
        allow_fallback: bool = False,
    ) -> dict:
        """
        Create an online payment link for a patient bill.
        If Paystack is unreachable and allow_fallback=True, falls back
        to Flutterwave automatically — keeping bill collection working
        during a provider outage.
        """
        tx_ref = f"CARENOVA-{self.country}-{uuid.uuid4().hex[:8].upper()}"

        if provider == "paystack":
            try:
                result = await self._call_paystack_api(
                    amount_ngn=amount_ngn,
                    patient_name=patient_name,
                    patient_phone=patient_phone,
                    description=description,
                    tx_ref=tx_ref,
                )
                return {
                    "provider": "paystack",
                    "payment_url": result["authorization_url"],
                    "reference": result["reference"],
                    "used_fallback": False,
                }
            except Exception as e:
                if not allow_fallback:
                    raise
                logger.warning(
                    "Paystack unreachable for clinic=%s, falling back to Flutterwave: %s",
                    self.clinic_id, e,
                )
                fw_result = await self._call_flutterwave_api(
                    amount_ngn=amount_ngn,
                    patient_name=patient_name,
                    patient_phone=patient_phone,
                    description=description,
                    tx_ref=tx_ref,
                )
                return {
                    "provider": "flutterwave",
                    "payment_url": fw_result["link"],
                    "reference": fw_result["tx_ref"],
                    "used_fallback": True,
                }

        elif provider == "flutterwave":
            result = await self._call_flutterwave_api(
                amount_ngn=amount_ngn,
                patient_name=patient_name,
                patient_phone=patient_phone,
                description=description,
                tx_ref=tx_ref,
            )
            return {
                "provider": "flutterwave",
                "payment_url": result["link"],
                "reference": result["tx_ref"],
                "used_fallback": False,
            }

        raise ValueError(f"Unknown online payment provider: {provider}")

    async def record_offline_payment(
        self,
        method: str,
        amount_ngn: float,
        patient_id: str,
        visit_id: str,
        received_by: str,
        pos_terminal_id: Optional[str] = None,
    ) -> dict:
        """
        Record a cash, POS, or bank transfer payment taken directly at
        the clinic desk — no online payment link involved.
        """
        if method not in VALID_OFFLINE_METHODS:
            raise ValueError(
                f"Invalid offline payment method '{method}'. "
                f"Must be one of: {VALID_OFFLINE_METHODS}"
            )

        record = {
            "id": f"PAY-{self.country}-{uuid.uuid4().hex[:8].upper()}",
            "clinic_id": self.clinic_id,
            "patient_id": patient_id,
            "visit_id": visit_id,
            "method": method,
            "amount_ngn": amount_ngn,
            "received_by": received_by,
            "pos_terminal_id": pos_terminal_id,
            "status": "completed",
            "recorded_at": datetime.utcnow().isoformat(),
        }

        saved = await self._save_payment_record(record)
        return {
            "payment_id": saved.get("id", record["id"]),
            "status": saved.get("status", "completed"),
            "method": method,
        }

    # ── External API stubs — replaced with real Paystack/Flutterwave calls ──

    async def _call_paystack_api(self, **kwargs) -> dict:
        """Production: POST to api.paystack.co/transaction/initialize"""
        return {"authorization_url": "", "reference": ""}

    async def _call_flutterwave_api(self, **kwargs) -> dict:
        """Production: POST to api.flutterwave.com/v3/payments"""
        return {"link": "", "tx_ref": ""}

    async def _save_payment_record(self, record: dict) -> dict:
        """Production: INSERT into patient_payments table."""
        return record
