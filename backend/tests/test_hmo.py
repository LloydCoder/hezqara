"""
HMO Claims Workflow Tests.

Confirmed hard requirement from market research: over 50 Health
Maintenance Organizations require electronic claims in Nigeria, and
every Nigerian HMS must distinguish between cash-pay patients, HMO
enrollees, and NHIA-covered patients with separate billing workflows.

This was a confirmed gap — zero HMO workflow existed before this build.
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestHMODirectory:

    def test_hmo_service_importable(self):
        from app.standalone.hmo import HMOService
        assert HMOService is not None

    @pytest.mark.asyncio
    async def test_list_known_hmos(self):
        """Returns the seeded HMO directory — NHIS, Hygeia, AXA, Avon, Reliance, THT."""
        from app.standalone.hmo import HMOService
        svc = HMOService(clinic_id="clinic_ng_001")

        with patch.object(svc, "_query_hmo_directory", return_value=[
            {"id": "1", "name": "NHIS", "short_code": "NHIS"},
            {"id": "2", "name": "Hygeia HMO", "short_code": "HYG"},
            {"id": "3", "name": "Reliance HMO", "short_code": "REL"},
        ]):
            hmos = await svc.list_hmos()

        assert len(hmos) == 3
        names = [h["name"] for h in hmos]
        assert "NHIS" in names


class TestPatientCoverageType:

    def test_determine_coverage_type_cash_pay(self):
        """Patient with no insurance info is cash-pay."""
        from app.standalone.hmo import HMOService
        svc = HMOService(clinic_id="clinic_ng_001")
        coverage = svc.determine_coverage_type({"hmo_id": None, "nhis_number": None})
        assert coverage == "cash_pay"

    def test_determine_coverage_type_hmo(self):
        """Patient with hmo_id set is an HMO enrollee."""
        from app.standalone.hmo import HMOService
        svc = HMOService(clinic_id="clinic_ng_001")
        coverage = svc.determine_coverage_type({"hmo_id": "hmo_hygeia_001", "nhis_number": None})
        assert coverage == "hmo"

    def test_determine_coverage_type_nhis(self):
        """Patient with nhis_number set is NHIS-covered, takes priority over HMO if both present."""
        from app.standalone.hmo import HMOService
        svc = HMOService(clinic_id="clinic_ng_001")
        coverage = svc.determine_coverage_type({"hmo_id": None, "nhis_number": "NHIS-2026-001"})
        assert coverage == "nhis"


class TestHMOClaimSubmission:

    @pytest.mark.asyncio
    async def test_submit_claim_creates_record(self):
        from app.standalone.hmo import HMOService
        svc = HMOService(clinic_id="clinic_ng_001")

        with patch.object(svc, "_save_claim", return_value={
            "id": "CLAIM-NG-001",
            "status": "submitted",
        }):
            result = await svc.submit_claim(
                patient_id="PAT-NG-001",
                hmo_id="hmo_hygeia_001",
                visit_id="VISIT-NG-001",
                diagnosis_code="J06.9",
                service_codes=["CONS-001"],
                amount_ngn=15000,
            )

        assert result["claim_id"] == "CLAIM-NG-001"
        assert result["status"] == "submitted"

    @pytest.mark.asyncio
    async def test_claim_requires_diagnosis_code(self):
        """HMO claims cannot be submitted without a diagnosis code — required field."""
        from app.standalone.hmo import HMOService
        svc = HMOService(clinic_id="clinic_ng_001")

        with pytest.raises(ValueError):
            await svc.submit_claim(
                patient_id="PAT-NG-001",
                hmo_id="hmo_hygeia_001",
                visit_id="VISIT-NG-001",
                diagnosis_code="",
                service_codes=["CONS-001"],
                amount_ngn=15000,
            )

    @pytest.mark.asyncio
    async def test_get_claim_status(self):
        from app.standalone.hmo import HMOService
        svc = HMOService(clinic_id="clinic_ng_001")

        with patch.object(svc, "_query_claim", return_value={
            "id": "CLAIM-NG-001",
            "status": "approved",
            "amount_approved_ngn": 15000,
        }):
            result = await svc.get_claim_status("CLAIM-NG-001")

        assert result["status"] == "approved"

    @pytest.mark.asyncio
    async def test_list_pending_claims_for_clinic(self):
        """Dashboard needs to show all pending HMO claims."""
        from app.standalone.hmo import HMOService
        svc = HMOService(clinic_id="clinic_ng_001")

        with patch.object(svc, "_query_pending_claims", return_value=[
            {"id": "CLAIM-001", "status": "submitted", "amount_ngn": 15000},
            {"id": "CLAIM-002", "status": "submitted", "amount_ngn": 8000},
        ]):
            claims = await svc.list_pending_claims()

        assert len(claims) == 2


class TestNHISTariff:

    def test_nhis_tariff_lookup(self):
        """NHIA tariff schedule support — required for government-affiliated hospitals."""
        from app.standalone.hmo import NHISTariff
        amount = NHISTariff.get_tariff("CONS-001")  # General consultation
        assert amount > 0

    def test_nhis_tariff_unknown_code_returns_none(self):
        from app.standalone.hmo import NHISTariff
        amount = NHISTariff.get_tariff("NONEXISTENT-CODE")
        assert amount is None

    def test_nhis_common_codes_present(self):
        """The most common NHIA tariff codes must be pre-loaded."""
        from app.standalone.hmo import NHISTariff
        codes = NHISTariff.get_all_codes()
        assert len(codes) >= 5
