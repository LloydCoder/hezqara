"""Tests for all 10 items built today."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# ── 1. Demo seed data ─────────────────────────────────────────────────────────

class TestDemoSeedData:
    def test_seed_data_importable(self):
        from app.demo.seed import SEED_DATA
        assert SEED_DATA is not None

    def test_us_clinic_present(self):
        from app.demo.seed import US_CLINIC
        assert US_CLINIC["id"] == "demo_clinic_us"
        assert US_CLINIC["ehr_type"] == "athenahealth"
        assert US_CLINIC["country"] == "US"

    def test_nigeria_clinic_present(self):
        from app.demo.seed import NG_CLINIC
        assert NG_CLINIC["id"] == "demo_clinic_ng"
        assert NG_CLINIC["ehr_type"] == "standalone"
        assert NG_CLINIC["country"] == "NG"

    def test_us_patients_present(self):
        from app.demo.seed import US_PATIENTS
        assert len(US_PATIENTS) >= 5
        names = [p["first_name"] for p in US_PATIENTS]
        assert "Maria" in names

    def test_nigeria_patients_present(self):
        from app.demo.seed import NG_PATIENTS
        assert len(NG_PATIENTS) >= 3
        names = [p["first_name"] for p in NG_PATIENTS]
        assert "Amaka" in names

    def test_demo_calls_present(self):
        from app.demo.seed import US_CALLS
        assert len(US_CALLS) >= 5
        intents = [c["intent"] for c in US_CALLS]
        assert "scheduling" in intents

    def test_analytics_has_all_periods(self):
        from app.demo.seed import DEMO_ANALYTICS
        assert "today" in DEMO_ANALYTICS
        assert "week" in DEMO_ANALYTICS
        assert "month" in DEMO_ANALYTICS

    def test_get_demo_analytics_function(self):
        from app.demo.seed import get_demo_analytics
        result = get_demo_analytics("today")
        assert result["total_calls"] > 0
        assert result["total_cost_savings_usd"] > 0

    def test_appointments_have_today_date(self):
        from app.demo.seed import US_APPOINTMENTS
        from datetime import date
        today = date.today().isoformat()
        assert all(today in a["appointment_datetime"] for a in US_APPOINTMENTS)


# ── 2. Standalone router ──────────────────────────────────────────────────────

class TestStandaloneRouter:
    def test_standalone_router_importable(self):
        from app.routers.standalone import router
        assert router is not None

    def test_standalone_router_has_correct_prefix(self):
        from app.routers.standalone import router
        assert router.prefix == "/standalone"

    def test_all_route_paths_defined(self):
        from app.routers.standalone import router
        paths = [r.path for r in router.routes]
        assert any("patients" in p for p in paths)
        assert any("slots" in p for p in paths)
        assert any("appointments" in p for p in paths)
        assert any("vitals" in p for p in paths)
        assert any("pre-visit" in p for p in paths)
        assert any("notes" in p for p in paths)
        assert any("csv" in p for p in paths)
        assert any("whatsapp" in p for p in paths)
        assert any("providers" in p for p in paths)
        assert any("pricing" in p for p in paths)
        assert any("upgrade" in p for p in paths)


# ── 3. HIPAA module ───────────────────────────────────────────────────────────

class TestHIPAAModule:
    def test_hipaa_importable(self):
        from app.compliance.hipaa import HIPAACompliance
        assert HIPAACompliance is not None

    def test_mask_phone_number(self):
        from app.compliance.hipaa import HIPAACompliance
        result = HIPAACompliance.mask_phone("+12125551234")
        assert "****" in result
        assert result != "+12125551234"

    def test_mask_phi_in_text(self):
        from app.compliance.hipaa import HIPAACompliance
        text = "Patient Maria Santos called from +12125551234"
        masked = HIPAACompliance.mask_phi(text)
        assert "+12125551234" not in masked or "****" in masked

    def test_contains_phi_detects_phone(self):
        from app.compliance.hipaa import HIPAACompliance
        assert HIPAACompliance.contains_phi("+12125551234") is True
        assert HIPAACompliance.contains_phi("Hello world") is False

    def test_audit_phi_access_returns_entry(self):
        from app.compliance.hipaa import HIPAACompliance
        entry = HIPAACompliance.audit_phi_access(
            clinic_id="clinic_001",
            user_id="user_001",
            patient_id="PAT-001",
            action="view",
            resource="patient_record",
        )
        assert entry["action"] == "view"
        assert entry["compliant"] is True

    def test_minimum_necessary_treatment(self):
        from app.compliance.hipaa import HIPAACompliance
        data = {"patient_id": "P1", "first_name": "Maria", "ssn": "123-45-6789",
                "insurance_carrier": "BlueCross", "diagnosis": "HTN"}
        result = HIPAACompliance.apply_minimum_necessary(data, "treatment")
        assert "diagnosis" in result  # Full access for treatment

    def test_minimum_necessary_operations(self):
        from app.compliance.hipaa import HIPAACompliance
        data = {"patient_id": "P1", "first_name": "Maria", "ssn": "123-45-6789",
                "insurance_carrier": "BlueCross", "diagnosis": "HTN"}
        result = HIPAACompliance.apply_minimum_necessary(data, "operations")
        assert "ssn" not in result
        assert "diagnosis" not in result

    def test_deidentify_removes_phi(self):
        from app.compliance.hipaa import HIPAACompliance
        patient = {"patient_id": "P1", "first_name": "Maria", "last_name": "Santos",
                   "phone": "+12125551234", "date_of_birth": "1985-03-15",
                   "insurance_carrier": "BlueCross"}
        result = HIPAACompliance.deidentify(patient)
        assert "first_name" not in result
        assert "phone" not in result
        assert "patient_id" not in result
        assert "anonymous_id" in result

    def test_baa_status_returns_all_partners(self):
        from app.compliance.hipaa import HIPAACompliance
        status = HIPAACompliance.get_baa_status()
        assert "retell_ai" in status
        assert "supabase" in status
        assert all(v["status"] == "signed" for v in status.values())

    def test_compliance_checklist_returns_score(self):
        from app.compliance.hipaa import HIPAACompliance
        clinic = {"hipaa_baa_signed": True, "ehr_type": "athenahealth"}
        result = HIPAACompliance.get_compliance_checklist(clinic)
        assert "score" in result
        assert result["score"] > 0
        assert result["passed"] > 0
        assert len(result["checks"]) >= 10


# ── 4. Checkout service ───────────────────────────────────────────────────────

class TestCheckoutService:
    def test_checkout_importable(self):
        from app.services.checkout import get_checkout_url
        assert get_checkout_url is not None

    def test_us_starter_uses_lemonsqueezy(self):
        from app.services.checkout import get_checkout_url
        result = get_checkout_url("starter", "US")
        assert result["provider"] == "lemonsqueezy"
        assert result["currency"] == "USD"
        assert result["amount"] == 499

    def test_us_pro_correct_price(self):
        from app.services.checkout import get_checkout_url
        result = get_checkout_url("pro", "US")
        assert result["amount"] == 999
        assert result["currency"] == "USD"

    def test_us_enterprise_uses_stripe(self):
        from app.services.checkout import get_checkout_url
        result = get_checkout_url("enterprise", "US")
        assert result["provider"] == "stripe"
        assert result["amount"] == 3999

    def test_nigeria_uses_paystack(self):
        from app.services.checkout import get_checkout_url
        result = get_checkout_url("starter", "NG")
        assert result["provider"] == "paystack"
        assert result["currency"] == "NGN"
        assert result["amount"] == 25_000

    def test_nigeria_pro_price(self):
        from app.services.checkout import get_checkout_url
        result = get_checkout_url("pro", "NG")
        assert result["amount"] == 49_000

    def test_get_all_checkout_urls(self):
        from app.services.checkout import get_all_checkout_urls
        result = get_all_checkout_urls("US")
        assert "starter" in result
        assert "pro" in result
        assert "growth" in result
        assert "enterprise" in result


# ── 5. Onboarding router ──────────────────────────────────────────────────────

class TestOnboardingRouter:
    def test_onboarding_router_importable(self):
        from app.routers.onboarding import router
        assert router is not None

    def test_onboarding_router_prefix(self):
        from app.routers.onboarding import router
        assert router.prefix == "/onboarding"

    def test_seven_steps_defined(self):
        from app.routers.onboarding import ONBOARDING_STEPS
        assert len(ONBOARDING_STEPS) == 7
        step_ids = [s["id"] for s in ONBOARDING_STEPS]
        assert "clinic_details" in step_ids
        assert "ehr_connection" in step_ids
        assert "voice_setup" in step_ids
        assert "baa_signing" in step_ids
        assert "go_live" in step_ids

    def test_all_routes_present(self):
        from app.routers.onboarding import router
        paths = [r.path for r in router.routes]
        assert any("status" in p for p in paths)
        assert any("clinic-details" in p for p in paths)
        assert any("/ehr" in p for p in paths)
        assert any("voice" in p for p in paths)
        assert any("agents" in p for p in paths)
        assert any("baa" in p for p in paths)
        assert any("test-call" in p for p in paths)
        assert any("go-live" in p for p in paths)


# ── 6. BAA service ────────────────────────────────────────────────────────────

class TestBAAService:
    def test_baa_importable(self):
        from app.compliance.baa import BAAService
        assert BAAService is not None

    def test_generate_baa_returns_document(self):
        from app.compliance.baa import BAAService
        result = BAAService.generate_baa(
            clinic_name="Family Care Associates",
            signatory_name="Dr. James Chen",
            signatory_title="Medical Director",
            signed_date="2026-07-01",
            clinic_id="clinic_001",
        )
        assert result["status"] == "signed"
        assert "BAA" in result["baa_reference"]
        assert "Family Care Associates" in result["text"]
        assert "Tinlance Limited" in result["text"]

    def test_baa_reference_format(self):
        from app.compliance.baa import BAAService
        result = BAAService.generate_baa(
            clinic_name="Test Clinic", signatory_name="Dr. Test",
            signatory_title="MD", signed_date="2026-07-01", clinic_id="abc12345",
        )
        assert result["baa_reference"].startswith("BAA-")
        assert "2026" in result["baa_reference"]

    def test_verify_baa_signed(self):
        from app.compliance.baa import BAAService
        clinic = {"hipaa_baa_signed": True, "baa_reference": "BAA-CLINIC-2026"}
        result = BAAService.verify_baa(clinic)
        assert result["signed"] is True

    def test_verify_baa_unsigned(self):
        from app.compliance.baa import BAAService
        clinic = {"hipaa_baa_signed": False}
        result = BAAService.verify_baa(clinic)
        assert result["signed"] is False
        assert "required" in result["message"].lower()


# ── 7. OpenMRS integration ────────────────────────────────────────────────────

class TestOpenMRSClient:
    def test_openmrs_importable(self):
        from app.ehr.openmrs import OpenMRSClient
        assert OpenMRSClient is not None

    def test_implements_base_ehr(self):
        from app.ehr.openmrs import OpenMRSClient
        from app.ehr.base import BaseEHR
        assert issubclass(OpenMRSClient, BaseEHR)

    def test_initialises_with_credentials(self):
        from app.ehr.openmrs import OpenMRSClient
        client = OpenMRSClient(
            base_url="https://openmrs.myhospital.ng/openmrs",
            username="admin",
            password="Admin123",
        )
        assert "openmrs" in client.api_base
        assert client.username == "admin"

    def test_api_base_url_constructed_correctly(self):
        from app.ehr.openmrs import OpenMRSClient
        client = OpenMRSClient(
            base_url="https://openmrs.hospital.ng/openmrs",
            username="admin", password="pass",
        )
        assert client.api_base == "https://openmrs.hospital.ng/openmrs/ws/rest/v1"

    @pytest.mark.asyncio
    async def test_get_patient_returns_none_on_failure(self):
        from app.ehr.openmrs import OpenMRSClient
        import httpx
        client = OpenMRSClient(
            base_url="https://openmrs.test/openmrs",
            username="admin", password="pass",
        )
        with patch.object(client, "_ensure_token", return_value="tok"):
            with patch("httpx.AsyncClient") as mock:
                mock.return_value.__aenter__.return_value.get = AsyncMock(
                    side_effect=httpx.ConnectError("unreachable")
                )
                result = await client.get_patient("clinic", "+2348031234567")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_patient_maps_correctly(self):
        from app.ehr.openmrs import OpenMRSClient
        client = OpenMRSClient(
            base_url="https://openmrs.test/openmrs",
            username="admin", password="pass",
        )
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "results": [{
                "uuid": "openmrs-uuid-001",
                "person": {
                    "names": [{"givenName": "Amaka", "familyName": "Obi", "preferred": True}],
                    "birthdate": "1990-03-15",
                    "gender": "F",
                    "attributes": [
                        {"attributeType": {"display": "Telephone Number"}, "value": "2348031234567"}
                    ],
                },
            }]
        }
        with patch.object(client, "_ensure_token", return_value="tok"):
            with patch("httpx.AsyncClient") as mock:
                mock.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
                result = await client.get_patient("clinic", "+2348031234567")
        assert result is not None
        assert result["first_name"] == "Amaka"
        assert result["patient_id"] == "openmrs-uuid-001"


# ── 8. Cerner scaffold ────────────────────────────────────────────────────────

class TestCernerClient:
    def test_cerner_importable(self):
        from app.ehr.cerner import CernerClient
        assert CernerClient is not None

    def test_implements_base_ehr(self):
        from app.ehr.cerner import CernerClient
        from app.ehr.base import BaseEHR
        assert issubclass(CernerClient, BaseEHR)

    def test_token_url_uses_tenant_id(self):
        from app.ehr.cerner import CernerClient
        client = CernerClient(
            client_id="id", client_secret="s",
            tenant_id="abc123-tenant",
        )
        assert "abc123-tenant" in client.token_url
        assert "cerner.com" in client.token_url

    def test_sandbox_url_is_default(self):
        from app.ehr.cerner import CernerClient, CERNER_FHIR_SANDBOX
        client = CernerClient(client_id="id", client_secret="s", tenant_id="t1")
        assert client.fhir_base_url == CERNER_FHIR_SANDBOX

    @pytest.mark.asyncio
    async def test_get_patient_returns_none_on_failure(self):
        from app.ehr.cerner import CernerClient
        import httpx
        client = CernerClient(client_id="id", client_secret="s", tenant_id="t1")
        with patch.object(client, "_ensure_token", return_value="tok"):
            with patch("httpx.AsyncClient") as mock:
                mock.return_value.__aenter__.return_value.get = AsyncMock(
                    side_effect=httpx.ConnectError("no Cerner")
                )
                result = await client.get_patient("clinic", "+12125551234")
        assert result is None


# ── 9. Email sequences ────────────────────────────────────────────────────────

class TestEmailSequences:
    def test_sequences_importable(self):
        from app.sequences.email_sequences import ALL_SEQUENCES
        assert ALL_SEQUENCES is not None

    def test_all_five_sequences_present(self):
        from app.sequences.email_sequences import ALL_SEQUENCES
        assert "clinic_onboarding_us" in ALL_SEQUENCES
        assert "clinic_onboarding_ng" in ALL_SEQUENCES
        assert "demo_followup" in ALL_SEQUENCES
        assert "trial_activation" in ALL_SEQUENCES
        assert "week_1_summary" in ALL_SEQUENCES

    def test_us_sequence_has_four_emails(self):
        from app.sequences.email_sequences import US_SEQUENCE
        assert len(US_SEQUENCE["emails"]) == 4

    def test_nigeria_sequence_in_correct_language(self):
        from app.sequences.email_sequences import NG_SEQUENCE
        body = NG_SEQUENCE["emails"][0]["body"]
        assert "₦" in body or "NGN" in body or "Nigerian" in body

    def test_week_1_summary_has_placeholders(self):
        from app.sequences.email_sequences import WEEK_1_SUMMARY
        body = WEEK_1_SUMMARY["emails"][0]["body"]
        assert "{{total_calls}}" in body
        assert "{{savings_usd}}" in body

    def test_get_sequence_function(self):
        from app.sequences.email_sequences import get_sequence
        result = get_sequence("clinic_onboarding_us")
        assert result["id"] == "clinic_onboarding_us"

    def test_get_sequence_returns_empty_for_unknown(self):
        from app.sequences.email_sequences import get_sequence
        result = get_sequence("unknown_sequence")
        assert result == {}


# ── 10. Marketplace applications ──────────────────────────────────────────────

class TestMarketplaceApplications:
    def test_marketplace_importable(self):
        from app.marketplace.applications import MARKETPLACE_CHECKLIST
        assert MARKETPLACE_CHECKLIST is not None

    def test_three_marketplaces_tracked(self):
        from app.marketplace.applications import MARKETPLACE_CHECKLIST
        assert "athenahealth" in MARKETPLACE_CHECKLIST
        assert "epic" in MARKETPLACE_CHECKLIST
        assert "oracle_health" in MARKETPLACE_CHECKLIST

    def test_athenahealth_application_has_listing_description(self):
        from app.marketplace.applications import ATHENAHEALTH_APPLICATION
        assert len(ATHENAHEALTH_APPLICATION["listing_description"]) > 100
        assert "athenahealth" in ATHENAHEALTH_APPLICATION["listing_description"].lower()

    def test_athenahealth_has_api_endpoints(self):
        from app.marketplace.applications import ATHENAHEALTH_APPLICATION
        assert len(ATHENAHEALTH_APPLICATION["api_endpoints_used"]) >= 5

    def test_medix_partnership_email_exists(self):
        from app.marketplace.applications import MEDIX_CONTACT
        assert len(MEDIX_CONTACT["email_template"]) > 100
        assert "Medix" in MEDIX_CONTACT["email_template"]
        assert "Tinlance" in MEDIX_CONTACT["email_template"]

    def test_oracle_health_notes_your_aunt(self):
        from app.marketplace.applications import ORACLE_HEALTH_APPLICATION
        assert "federal" in ORACLE_HEALTH_APPLICATION["why_priority"].lower() or \
               "hospital" in ORACLE_HEALTH_APPLICATION["why_priority"].lower()

    def test_all_marketplaces_not_yet_applied(self):
        from app.marketplace.applications import MARKETPLACE_CHECKLIST
        # Should all be False — we haven't applied yet
        for mkt, status in MARKETPLACE_CHECKLIST.items():
            assert status["applied"] is False, f"{mkt} should not be marked as applied yet"


# ── EHR registry completeness check ──────────────────────────────────────────

class TestEHRRegistryComplete:
    def test_all_15_ehr_clients_importable(self):
        from app.ehr.athenahealth import AthenaHealthClient
        from app.ehr.modmed import ModMedClient
        from app.ehr.helium_health import HeliumHealthClient
        from app.ehr.openmrs import OpenMRSClient
        from app.ehr.cerner import CernerClient
        from app.ehr.ehr_integrations import (
            NextGenClient, EClinicalWorksClient, EpicClient,
            DrChronoClient, ElationHealthClient, TebraClient,
            PracticeFusionClient, AdvancedMDClient,
            TherapyNotesClient, PCCClient,
        )
        from app.ehr.base import BaseEHR

        all_clients = [
            AthenaHealthClient, ModMedClient, HeliumHealthClient,
            OpenMRSClient, CernerClient,
            NextGenClient, EClinicalWorksClient, EpicClient,
            DrChronoClient, ElationHealthClient, TebraClient,
            PracticeFusionClient, AdvancedMDClient,
            TherapyNotesClient, PCCClient,
        ]
        assert len(all_clients) == 15
        for cls in all_clients:
            assert issubclass(cls, BaseEHR), f"{cls.__name__} must implement BaseEHR"
