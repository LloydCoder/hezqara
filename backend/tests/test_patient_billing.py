"""
Patient Bill Collection Tests — Nigeria payment rails.

Distinct from app/services/checkout.py, which handles Carenova's own
SaaS subscription billing (clinic pays Carenova). This module handles
PATIENT bill collection at the clinic (patient pays the clinic for
their visit) — confirmed gap: Nigerian HMS must integrate with local
payment gateways (Paystack, Flutterwave, bank transfers) for both
online and POS payments, and only Paystack existed before this build.
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestPatientBillCollection:

    def test_bill_collection_importable(self):
        from app.standalone.billing import PatientBillingService
        assert PatientBillingService is not None

    def test_available_payment_methods_nigeria(self):
        """Nigerian clinics need cash, POS, bank transfer, Paystack, Flutterwave."""
        from app.standalone.billing import PatientBillingService
        svc = PatientBillingService(clinic_id="clinic_ng_001", country="NG")
        methods = svc.get_available_payment_methods()
        method_ids = [m["id"] for m in methods]
        assert "cash" in method_ids
        assert "pos" in method_ids
        assert "bank_transfer" in method_ids
        assert "paystack" in method_ids
        assert "flutterwave" in method_ids

    def test_available_payment_methods_us(self):
        """US clinics use card/insurance, not Nigeria-specific rails."""
        from app.standalone.billing import PatientBillingService
        svc = PatientBillingService(clinic_id="clinic_us_001", country="US")
        methods = svc.get_available_payment_methods()
        method_ids = [m["id"] for m in methods]
        assert "card" in method_ids
        assert "pos" not in method_ids  # Not a US concept in this context

    @pytest.mark.asyncio
    async def test_create_flutterwave_payment_link(self):
        from app.standalone.billing import PatientBillingService
        svc = PatientBillingService(clinic_id="clinic_ng_001", country="NG")

        with patch.object(svc, "_call_flutterwave_api", return_value={
            "link": "https://checkout.flutterwave.com/pay/abc123",
            "tx_ref": "CARENOVA-NG-001",
        }):
            result = await svc.create_payment_link(
                provider="flutterwave",
                amount_ngn=15000,
                patient_name="Amaka Obi",
                patient_phone="+2348031234567",
                description="Consultation fee",
            )

        assert "flutterwave.com" in result["payment_url"]
        assert result["provider"] == "flutterwave"

    @pytest.mark.asyncio
    async def test_create_paystack_payment_link(self):
        from app.standalone.billing import PatientBillingService
        svc = PatientBillingService(clinic_id="clinic_ng_001", country="NG")

        with patch.object(svc, "_call_paystack_api", return_value={
            "authorization_url": "https://checkout.paystack.com/abc123",
            "reference": "CARENOVA-NG-002",
        }):
            result = await svc.create_payment_link(
                provider="paystack",
                amount_ngn=15000,
                patient_name="Amaka Obi",
                patient_phone="+2348031234567",
                description="Consultation fee",
            )

        assert "paystack.com" in result["payment_url"]
        assert result["provider"] == "paystack"

    @pytest.mark.asyncio
    async def test_record_cash_payment(self):
        """Cash and POS payments are recorded directly — no payment link needed."""
        from app.standalone.billing import PatientBillingService
        svc = PatientBillingService(clinic_id="clinic_ng_001", country="NG")

        with patch.object(svc, "_save_payment_record", return_value={
            "id": "PAY-NG-001", "status": "completed",
        }):
            result = await svc.record_offline_payment(
                method="cash",
                amount_ngn=15000,
                patient_id="PAT-NG-001",
                visit_id="VISIT-NG-001",
                received_by="Nurse Amaka",
            )

        assert result["status"] == "completed"
        assert result["method"] == "cash"

    @pytest.mark.asyncio
    async def test_record_pos_payment(self):
        from app.standalone.billing import PatientBillingService
        svc = PatientBillingService(clinic_id="clinic_ng_001", country="NG")

        with patch.object(svc, "_save_payment_record", return_value={
            "id": "PAY-NG-002", "status": "completed",
        }):
            result = await svc.record_offline_payment(
                method="pos",
                amount_ngn=15000,
                patient_id="PAT-NG-001",
                visit_id="VISIT-NG-001",
                received_by="Nurse Amaka",
                pos_terminal_id="TERM-001",
            )

        assert result["method"] == "pos"

    @pytest.mark.asyncio
    async def test_invalid_payment_method_rejected(self):
        from app.standalone.billing import PatientBillingService
        svc = PatientBillingService(clinic_id="clinic_ng_001", country="NG")

        with pytest.raises(ValueError):
            await svc.record_offline_payment(
                method="cryptocurrency",
                amount_ngn=15000,
                patient_id="PAT-NG-001",
                visit_id="VISIT-NG-001",
                received_by="Nurse Amaka",
            )

    @pytest.mark.asyncio
    async def test_flutterwave_used_as_paystack_fallback(self):
        """If Paystack is unreachable, Flutterwave should be offered as fallback."""
        from app.standalone.billing import PatientBillingService
        svc = PatientBillingService(clinic_id="clinic_ng_001", country="NG")

        with patch.object(svc, "_call_paystack_api", side_effect=ConnectionError("down")):
            with patch.object(svc, "_call_flutterwave_api", return_value={
                "link": "https://checkout.flutterwave.com/pay/fallback123",
                "tx_ref": "FALLBACK-001",
            }):
                result = await svc.create_payment_link(
                    provider="paystack",
                    amount_ngn=15000,
                    patient_name="Amaka Obi",
                    patient_phone="+2348031234567",
                    description="Consultation fee",
                    allow_fallback=True,
                )

        assert result["provider"] == "flutterwave"
        assert result.get("used_fallback") is True
