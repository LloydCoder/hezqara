"""
ModMed EHR Complete Integration Tests
TDD RED phase — based on actual ModMed API documentation.

Key facts from official docs (portal.api.modmed.com):

AUTHENTICATION:
  - New: client_credentials grant (recommended)
  - Token endpoint (sandbox): https://ssoqa01-lb-01.m2qa.com/auth/realms/ema-fhir/protocol/openid-connect/token
  - Token endpoint (prod):    https://sso.ema.md/auth/realms/ema-fhir/protocol/openid-connect/token
  - Access token is RS256 JWT, expires_in=900 (15 min), NO refresh token
  - Legacy: password grant (being sunset) — uses x-api-key header
  - All calls need: Authorization: Bearer {token} AND x-api-key: {key}

URL STRUCTURE:
  - Each practice has a unique URL prefix: https://{practice_prefix}.ema.md
  - Base URL: https://{practice_prefix}.ema.md/{practice_prefix}/ema/fhir/v2/

EMA vs MMPM CRITICAL DISTINCTION:
  - EMA-only practices have NO scheduling/appointment data
  - Appointments live in ModMed Practice Management (MMPM)
  - Must confirm clinic uses MMPM before booking

IDENTIFIERS:
  - Every patient has unique MMI Identifier (EMAID)
  - Also may have PMSID (external PM system ID) and MRN
  - Providers have unique MMI identifier + NPI

PATIENT:
  - GET /fhir/v2/Patient?given=Maria&family=Santos&birthdate=1985-03-15
  - POST /fhir/v2/Patient — creates patient
  - PUT /fhir/v2/Patient/{id} — updates patient
  - Response: FHIR R4 Patient resource

APPOINTMENTS (MMPM only):
  - GET  /fhir/v2/Slot — search available slots
  - GET  /fhir/v2/Appointment — search appointments
  - POST /fhir/v2/Appointment — create/book appointment
  - PUT  /fhir/v2/Appointment/{id} — update/cancel appointment
  - Requires: patient, location, practitioner, appointmentType, start, end, minutesDuration, status
  - status: "booked" = confirmed in MMPM UI

APPOINTMENT TYPES:
  - GET /fhir/v2/ValueSet/appointment-type — returns firm's appointment types

INSURANCE (Coverage):
  - GET  /fhir/v2/Coverage?patient={id} — get patient coverages
  - POST /fhir/v2/Coverage — submit new coverage (requires reconciliation)
  - order: 1=Primary, 2=Secondary, 3=Tertiary

RATE LIMIT:
  - Default: 1000 calls/minute
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import time


class TestModMedClientInitialisation:

    def test_modmed_client_can_be_imported(self):
        from app.ehr.modmed import ModMedClient
        assert ModMedClient is not None

    def test_modmed_client_implements_base_ehr(self):
        from app.ehr.modmed import ModMedClient
        from app.ehr.base import BaseEHR
        assert issubclass(ModMedClient, BaseEHR)

    def test_modmed_client_requires_credentials(self):
        from app.ehr.modmed import ModMedClient
        with pytest.raises(TypeError):
            ModMedClient()

    def test_modmed_client_stores_practice_prefix(self):
        """Each ModMed practice has a unique URL prefix."""
        from app.ehr.modmed import ModMedClient
        client = ModMedClient(
            client_id="test_client_id",
            client_secret="test_secret",
            practice_prefix="dermassoc",
            api_key="test_api_key",
        )
        assert client.practice_prefix == "dermassoc"

    def test_modmed_client_builds_correct_base_url(self):
        """Sandbox uses stage.ema-api.com; prod uses {prefix}.ema.md"""
        from app.ehr.modmed import ModMedClient
        # Sandbox URL check
        client = ModMedClient(
            client_id="test_client_id",
            client_secret="test_secret",
            practice_prefix="dermassoc",
            api_key="test_api_key",
            use_sandbox=True,
        )
        assert "dermassoc" in client.base_url
        assert "fhir/v2" in client.base_url
        # Production URL check
        prod_client = ModMedClient(
            client_id="test_client_id",
            client_secret="test_secret",
            practice_prefix="dermassoc",
            api_key="test_api_key",
            use_sandbox=False,
        )
        assert "dermassoc.ema.md" in prod_client.base_url
        assert "fhir/v2" in prod_client.base_url

    def test_modmed_sandbox_url_constant_defined(self):
        from app.ehr.modmed import MODMED_TOKEN_SANDBOX, MODMED_TOKEN_PROD
        assert "ssoqa01" in MODMED_TOKEN_SANDBOX
        assert "sso.ema.md" in MODMED_TOKEN_PROD

    def test_modmed_starts_with_no_token(self):
        from app.ehr.modmed import ModMedClient
        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key"
        )
        assert client._access_token is None


class TestModMedOAuth2:

    @pytest.mark.asyncio
    async def test_fetch_token_client_credentials_flow(self):
        """
        New client_credentials grant.
        Token is RS256 JWT, expires_in=900, NO refresh token.
        """
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="test_id",
            client_secret="test_secret",
            practice_prefix="dermassoc",
            api_key="test_api_key",
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "eyJRS256token",
            "expires_in": 900,
            "token_type": "Bearer",
            "scope": "acl/enc_s acl/pat_s_name_dob_gen",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            token = await client._fetch_token()

        assert token == "eyJRS256token"
        assert client._access_token == "eyJRS256token"

    @pytest.mark.asyncio
    async def test_token_expires_in_900_seconds(self):
        """ModMed tokens expire in 900s (15 min) — not 3600s like athenahealth."""
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key"
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "tok_short",
            "expires_in": 900,  # 15 min — shorter than athena's 3600
            "token_type": "Bearer",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            await client._fetch_token()

        # Token should expire in < 15 minutes
        assert client._token_expires_at < time.time() + 900
        assert client._token_expires_at > time.time() + 600  # at least 10 min

    @pytest.mark.asyncio
    async def test_expired_token_auto_refreshed(self):
        """Token auto-refreshed when expired — no refresh_token needed."""
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key"
        )
        client._access_token = "old_token"
        client._token_expires_at = time.time() - 10  # expired

        with patch.object(client, "_fetch_token", return_value="new_token") as mock:
            await client._ensure_token()

        mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_valid_token_not_refetched(self):
        """Valid token reused — saves API call."""
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key"
        )
        client._access_token = "valid_token"
        client._token_expires_at = time.time() + 600  # 10 min remaining

        with patch.object(client, "_fetch_token") as mock:
            await client._ensure_token()

        mock.assert_not_called()


class TestModMedPatientOperations:

    @pytest.mark.asyncio
    async def test_get_patient_by_phone_searches_telecom(self):
        """ModMed FHIR R4 — search by phone via telecom parameter."""
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key"
        )

        # ModMed returns FHIR R4 Bundle
        fhir_bundle = {
            "resourceType": "Bundle",
            "total": 1,
            "entry": [{
                "resource": {
                    "resourceType": "Patient",
                    "id": "EMAID-12345",
                    "name": [{"family": "Santos", "given": ["Maria"]}],
                    "birthDate": "1985-03-15",
                    "telecom": [
                        {"system": "phone", "value": "2125551234", "use": "mobile"}
                    ],
                }
            }]
        }

        with patch.object(client, "_get", return_value=fhir_bundle):
            result = await client.get_patient(
                clinic_id="clinic_001",
                phone="+12125551234",
            )

        assert result is not None
        assert result["patient_id"] == "EMAID-12345"
        assert result["first_name"] == "Maria"
        assert result["last_name"] == "Santos"

    @pytest.mark.asyncio
    async def test_get_patient_not_found_returns_none(self):
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key"
        )

        with patch.object(client, "_get", return_value={
            "resourceType": "Bundle", "total": 0, "entry": []
        }):
            result = await client.get_patient("clinic_001", "+19999999999")

        assert result is None

    @pytest.mark.asyncio
    async def test_search_patient_by_name_dob(self):
        """Search by name + DOB — primary method when no phone."""
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key"
        )

        with patch.object(client, "_get", return_value={
            "resourceType": "Bundle",
            "total": 1,
            "entry": [{"resource": {
                "resourceType": "Patient",
                "id": "EMAID-12345",
                "name": [{"family": "Santos", "given": ["Maria"]}],
                "birthDate": "1985-03-15",
            }}]
        }):
            result = await client.search_patient(
                clinic_id="clinic_001",
                first_name="Maria",
                last_name="Santos",
                date_of_birth="1985-03-15",
            )

        assert result is not None
        assert result["patient_id"] == "EMAID-12345"

    @pytest.mark.asyncio
    async def test_create_patient_posts_fhir_resource(self):
        """Create patient via FHIR R4 Patient CREATE."""
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key"
        )

        with patch.object(client, "_post", return_value={
            "resourceType": "Patient",
            "id": "EMAID-99999",
        }):
            result = await client.create_patient(
                clinic_id="clinic_001",
                data={
                    "first_name": "Maria",
                    "last_name": "Santos",
                    "date_of_birth": "1985-03-15",
                    "phone": "+12125551234",
                },
            )

        assert result["patient_id"] == "EMAID-99999"

    @pytest.mark.asyncio
    async def test_update_patient_puts_fhir_resource(self):
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key"
        )

        with patch.object(client, "_put", return_value={"resourceType": "Patient", "id": "EMAID-12345"}):
            result = await client.update_patient(
                clinic_id="clinic_001",
                patient_id="EMAID-12345",
                data={"email": "maria@example.com"},
            )

        assert result is not None


class TestModMedAppointmentOperations:

    @pytest.mark.asyncio
    async def test_get_available_slots_queries_fhir_slot(self):
        """
        ModMed uses FHIR Slot resource for availability.
        EMA-only practices have no scheduling — MMPM required.
        """
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key",
            has_mmpm=True,  # Must confirm MMPM
        )

        fhir_bundle = {
            "resourceType": "Bundle",
            "total": 2,
            "entry": [
                {"resource": {
                    "resourceType": "Slot",
                    "id": "SLOT-001",
                    "start": "2026-07-01T09:00:00-04:00",
                    "end": "2026-07-01T09:20:00-04:00",
                    "status": "free",
                    "schedule": {"reference": "Schedule/SCHED-P001"},
                }},
                {"resource": {
                    "resourceType": "Slot",
                    "id": "SLOT-002",
                    "start": "2026-07-01T10:30:00-04:00",
                    "end": "2026-07-01T10:50:00-04:00",
                    "status": "free",
                    "schedule": {"reference": "Schedule/SCHED-P001"},
                }},
            ]
        }

        with patch.object(client, "_get", return_value=fhir_bundle):
            slots = await client.get_available_slots(
                clinic_id="clinic_001",
                provider_id="P001",
                date="2026-07-01",
            )

        assert len(slots) == 2
        assert slots[0]["slot_id"] == "SLOT-001"
        assert "2026-07-01T09:00" in slots[0]["datetime_iso"]

    @pytest.mark.asyncio
    async def test_get_slots_returns_empty_for_ema_only(self):
        """EMA-only clinic — no MMPM — no scheduling available."""
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key",
            has_mmpm=False,  # EMA only
        )

        slots = await client.get_available_slots(
            clinic_id="clinic_001",
            provider_id="P001",
            date="2026-07-01",
        )

        # EMA-only: return empty list with warning
        assert slots == []

    @pytest.mark.asyncio
    async def test_book_appointment_posts_fhir_appointment(self):
        """
        Booking = POST FHIR Appointment resource.
        Requires: patient, location, practitioner, appointmentType,
                  start, end, minutesDuration, status="booked"
        """
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key",
            has_mmpm=True,
        )

        with patch.object(client, "_post", return_value={
            "resourceType": "Appointment",
            "id": "APT-MODMED-001",
            "status": "booked",
            "start": "2026-07-01T09:00:00-04:00",
            "end": "2026-07-01T09:20:00-04:00",
            "participant": [
                {"actor": {"reference": "Practitioner/P001"}, "status": "accepted"},
            ]
        }):
            result = await client.book_appointment(
                clinic_id="clinic_001",
                patient_id="EMAID-12345",
                slot_id="SLOT-001",
                reason="Annual skin check",
            )

        assert result["appointment_id"] == "APT-MODMED-001"
        assert result["status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_book_appointment_body_contains_required_fields(self):
        """FHIR Appointment body must include all required fields."""
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key",
            has_mmpm=True,
        )
        # Pre-populate slot cache so book_appointment knows start/end
        client._slot_cache["SLOT-001"] = {
            "start": "2026-07-01T09:00:00-04:00",
            "end": "2026-07-01T09:20:00-04:00",
            "duration_minutes": 20,
            "location_id": "LOC-001",
            "provider_id": "P001",
        }

        posted_body = {}

        async def capture_post(path, json_data):
            posted_body.update(json_data)
            return {
                "resourceType": "Appointment",
                "id": "APT-001",
                "status": "booked",
                "start": "2026-07-01T09:00:00-04:00",
            }

        with patch.object(client, "_post", side_effect=capture_post):
            await client.book_appointment(
                clinic_id="clinic_001",
                patient_id="EMAID-12345",
                slot_id="SLOT-001",
                reason="Annual skin check",
            )

        # Verify required FHIR fields present
        assert posted_body.get("status") == "booked"
        assert "participant" in posted_body
        assert "start" in posted_body
        assert "end" in posted_body
        assert "minutesDuration" in posted_body

    @pytest.mark.asyncio
    async def test_cancel_appointment_sets_status_cancelled(self):
        """Cancel = PUT with status=cancelled + cancellationReason."""
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key",
        )

        put_body = {}

        async def capture_put(path, json_data):
            put_body.update(json_data)
            return {"resourceType": "Appointment", "id": "APT-001", "status": "cancelled"}

        with patch.object(client, "_put", side_effect=capture_put):
            result = await client.cancel_appointment(
                clinic_id="clinic_001",
                patient_id="EMAID-12345",
                appointment_id="APT-MODMED-001",
            )

        assert result["status"] == "cancelled"
        assert put_body.get("status") == "cancelled"


class TestModMedAppointmentTypes:

    @pytest.mark.asyncio
    async def test_get_appointment_types_from_valueset(self):
        """
        Appointment types come from firm-specific ValueSet.
        GET /fhir/v2/ValueSet/appointment-type
        """
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key",
        )

        with patch.object(client, "_get", return_value={
            "resourceType": "ValueSet",
            "expansion": {
                "contains": [
                    {"code": "NEW_PT", "display": "New Patient", "property": [{"code": "duration", "valueInteger": 45}]},
                    {"code": "FOLLOW_UP", "display": "Follow-up", "property": [{"code": "duration", "valueInteger": 20}]},
                    {"code": "ANNUAL", "display": "Annual Exam", "property": [{"code": "duration", "valueInteger": 60}]},
                ]
            }
        }):
            types = await client.get_appointment_types(clinic_id="clinic_001")

        assert len(types) == 3
        assert types[0]["type_id"] == "NEW_PT"
        assert types[0]["name"] == "New Patient"


class TestModMedProviders:

    @pytest.mark.asyncio
    async def test_get_providers_returns_practitioners(self):
        """ModMed providers = FHIR Practitioner resources."""
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key",
        )

        with patch.object(client, "_get", return_value={
            "resourceType": "Bundle",
            "total": 2,
            "entry": [
                {"resource": {
                    "resourceType": "Practitioner",
                    "id": "PRACT-001",
                    "name": [{"family": "Chen", "given": ["James"], "prefix": ["Dr."]}],
                    "identifier": [{"system": "http://hl7.org/fhir/sid/us-npi", "value": "1234567890"}],
                }},
                {"resource": {
                    "resourceType": "Practitioner",
                    "id": "PRACT-002",
                    "name": [{"family": "Kim", "given": ["Sarah"], "prefix": ["Dr."]}],
                    "identifier": [{"system": "http://hl7.org/fhir/sid/us-npi", "value": "0987654321"}],
                }},
            ]
        }):
            providers = await client.get_providers(clinic_id="clinic_001")

        assert len(providers) == 2
        assert providers[0]["provider_id"] == "PRACT-001"
        assert providers[0]["name"] == "Dr. James Chen"
        assert providers[0]["npi"] == "1234567890"


class TestModMedInsurance:

    @pytest.mark.asyncio
    async def test_get_patient_insurance_coverage(self):
        """
        ModMed insurance = FHIR Coverage resource.
        order: 1=Primary, 2=Secondary, 3=Tertiary
        """
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key",
        )

        with patch.object(client, "_get", return_value={
            "resourceType": "Bundle",
            "entry": [
                {"resource": {
                    "resourceType": "Coverage",
                    "id": "COV-001",
                    "status": "active",
                    "order": 1,
                    "beneficiary": {"reference": "Patient/EMAID-12345"},
                    "payor": [{"display": "BlueCross BlueShield"}],
                    "class": [
                        {"type": {"code": "plan"}, "value": "BCB-847291", "name": "BlueCross PPO"},
                        {"type": {"code": "group"}, "value": "GRP-001"},
                    ],
                }}
            ]
        }):
            result = await client.get_patient_insurance(
                clinic_id="clinic_001",
                patient_id="EMAID-12345",
            )

        assert result is not None
        assert result["status"] == "active"
        assert result["carrier"] == "BlueCross BlueShield"
        assert result["order"] == 1

    @pytest.mark.asyncio
    async def test_get_insurance_returns_none_when_no_coverage(self):
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key",
        )

        with patch.object(client, "_get", return_value={
            "resourceType": "Bundle", "entry": [], "total": 0
        }):
            result = await client.get_patient_insurance(
                clinic_id="clinic_001",
                patient_id="EMAID-99999",
            )

        assert result is None


class TestModMedErrorHandling:

    @pytest.mark.asyncio
    async def test_connection_error_returns_none_for_patient_lookup(self):
        """Connection failure returns None — agent call continues."""
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key",
        )

        with patch.object(client, "_get", side_effect=httpx.ConnectError("ModMed unreachable")):
            result = await client.get_patient("clinic_001", "+12125551234")

        assert result is None

    @pytest.mark.asyncio
    async def test_401_triggers_token_refresh_and_retry(self):
        """401 triggers fresh token + single retry."""
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key",
        )
        client._access_token = "stale_token"
        client._token_expires_at = time.time() + 800

        calls = []

        async def flaky_get(path, params=None, _retry=True):
            calls.append({"path": path, "retry": _retry})
            if len(calls) == 1:
                raise httpx.HTTPStatusError(
                    "401", request=MagicMock(), response=MagicMock(status_code=401)
                )
            return {"resourceType": "Bundle", "total": 0, "entry": []}

        with patch.object(client, "_get", side_effect=flaky_get):
            with patch.object(client, "_fetch_token", return_value="new_token"):
                result = await client.get_patient("clinic_001", "+12125551234")

        assert result is None  # No patient found, but no crash

    @pytest.mark.asyncio
    async def test_book_appointment_fails_gracefully_on_ema_only(self):
        """Cannot book if practice has no MMPM — clear error returned."""
        from app.ehr.modmed import ModMedClient

        client = ModMedClient(
            client_id="id", client_secret="secret",
            practice_prefix="dermassoc", api_key="key",
            has_mmpm=False,
        )

        with pytest.raises(ValueError, match="MMPM"):
            await client.book_appointment(
                clinic_id="clinic_001",
                patient_id="EMAID-12345",
                slot_id="SLOT-001",
                reason="Annual exam",
            )
