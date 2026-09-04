"""
athenahealth EHR Integration Tests — Sprint 7
TDD RED phase.

athenahealth is the first EHR target — 160K providers.
Uses REST API + FHIR R4.

Abstract base defines the interface.
AthenaHealthClient implements it.
All agents use base interface — swapping EHR needs zero agent code changes.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestBaseEHRInterface:
    """Abstract EHR interface enforces the contract."""

    def test_base_ehr_can_be_imported(self):
        from app.ehr.base import BaseEHR
        assert BaseEHR is not None

    def test_base_ehr_is_abstract(self):
        """Cannot instantiate BaseEHR directly."""
        from app.ehr.base import BaseEHR
        with pytest.raises(TypeError):
            BaseEHR()

    def test_base_ehr_defines_required_methods(self):
        """All required methods are declared on BaseEHR."""
        from app.ehr.base import BaseEHR
        required = [
            "get_patient",
            "create_patient",
            "update_patient",
            "get_available_slots",
            "book_appointment",
            "cancel_appointment",
        ]
        for method in required:
            assert hasattr(BaseEHR, method), f"BaseEHR missing: {method}"


class TestAthenaHealthClientInitialisation:

    def test_athena_client_can_be_imported(self):
        from app.ehr.athenahealth import AthenaHealthClient
        assert AthenaHealthClient is not None

    def test_athena_client_implements_base_ehr(self):
        from app.ehr.athenahealth import AthenaHealthClient
        from app.ehr.base import BaseEHR
        assert issubclass(AthenaHealthClient, BaseEHR)

    def test_athena_client_requires_credentials(self):
        from app.ehr.athenahealth import AthenaHealthClient
        with pytest.raises(TypeError):
            AthenaHealthClient()

    def test_athena_client_stores_practice_id(self):
        from app.ehr.athenahealth import AthenaHealthClient
        client = AthenaHealthClient(
            client_id="test_id",
            client_secret="test_secret",
            practice_id="195900",
        )
        assert client.practice_id == "195900"


class TestAthenaHealthPatientOperations:

    @pytest.mark.asyncio
    async def test_get_patient_by_phone_returns_patient(self):
        """Patient lookup by phone returns patient dict."""
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="test_id",
            client_secret="test_secret",
            practice_id="195900",
        )

        mock_response = {
            "patients": [{
                "patientid": "12345",
                "firstname": "Maria",
                "lastname": "Santos",
                "mobilephone": "2125551234",
            }]
        }

        with patch.object(client, "_get", return_value=mock_response):
            result = await client.get_patient(
                clinic_id="clinic_test_001",
                phone="+12125551234",
            )

        assert result is not None
        assert result["patient_id"] == "12345"

    @pytest.mark.asyncio
    async def test_get_patient_not_found_returns_none(self):
        """Unknown patient returns None — not an error."""
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="test_id",
            client_secret="test_secret",
            practice_id="195900",
        )

        with patch.object(client, "_get", return_value={"patients": []}):
            result = await client.get_patient(
                clinic_id="clinic_test_001",
                phone="+19999999999",
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_create_patient_returns_patient_id(self):
        """New patient creation returns athenahealth patient ID."""
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="test_id",
            client_secret="test_secret",
            practice_id="195900",
        )

        mock_response = [{"patientid": "67890"}]

        with patch.object(client, "_post", return_value=mock_response):
            result = await client.create_patient(
                clinic_id="clinic_test_001",
                data={
                    "first_name": "Maria",
                    "last_name": "Santos",
                    "date_of_birth": "1985-03-15",
                    "phone": "+12125551234",
                },
            )

        assert result["patient_id"] == "67890"

    @pytest.mark.asyncio
    async def test_update_patient_returns_success(self):
        """Patient update returns success dict."""
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="test_id",
            client_secret="test_secret",
            practice_id="195900",
        )

        with patch.object(client, "_put", return_value={"status": "success"}):
            result = await client.update_patient(
                clinic_id="clinic_test_001",
                patient_id="12345",
                data={"email": "maria@example.com"},
            )

        assert result is not None


class TestAthenaHealthAppointmentOperations:

    @pytest.mark.asyncio
    async def test_get_available_slots_returns_list(self):
        """Available slots returned as list of dicts."""
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="test_id",
            client_secret="test_secret",
            practice_id="195900",
        )

        mock_response = {
            "appointments": [
                {"appointmentid": "S001", "date": "07/01/2026", "starttime": "09:00", "providerid": "P001"},
                {"appointmentid": "S002", "date": "07/01/2026", "starttime": "10:30", "providerid": "P001"},
            ]
        }

        with patch.object(client, "_get", return_value=mock_response):
            slots = await client.get_available_slots(
                clinic_id="clinic_test_001",
                provider_id="P001",
                date="2026-07-01",
            )

        assert len(slots) == 2
        assert slots[0]["slot_id"] == "S001"

    @pytest.mark.asyncio
    async def test_book_appointment_returns_confirmation(self):
        """Appointment booking returns confirmation with appointment_id."""
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="test_id",
            client_secret="test_secret",
            practice_id="195900",
        )

        mock_response = {"appointmentid": "APT001", "status": "f"}

        with patch.object(client, "_put", return_value=mock_response):
            result = await client.book_appointment(
                clinic_id="clinic_test_001",
                patient_id="12345",
                slot_id="S001",
                reason="Annual checkup",
            )

        assert result["appointment_id"] == "APT001"
        assert result["status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_cancel_appointment_returns_success(self):
        """Appointment cancellation returns success."""
        from app.ehr.athenahealth import AthenaHealthClient

        client = AthenaHealthClient(
            client_id="test_id",
            client_secret="test_secret",
            practice_id="195900",
        )

        with patch.object(client, "_put", return_value={"status": "x"}):
            result = await client.cancel_appointment(
                clinic_id="clinic_test_001",
                patient_id="12345",
                appointment_id="APT001",
            )

        assert result["status"] == "cancelled"


class TestFHIRMapper:

    def test_fhir_mapper_can_be_imported(self):
        from app.ehr.fhir_mapper import FHIRMapper
        assert FHIRMapper is not None

    def test_map_patient_to_fhir_resource(self):
        """Internal patient dict maps to valid FHIR Patient resource."""
        from app.ehr.fhir_mapper import FHIRMapper

        mapper = FHIRMapper()
        patient = {
            "patient_id": "12345",
            "first_name": "Maria",
            "last_name": "Santos",
            "date_of_birth": "1985-03-15",
            "phone": "+12125551234",
        }

        fhir = mapper.patient_to_fhir(patient)

        assert fhir["resourceType"] == "Patient"
        assert fhir["id"] == "12345"
        assert fhir["name"][0]["family"] == "Santos"
        assert fhir["name"][0]["given"][0] == "Maria"

    def test_map_fhir_appointment_to_internal(self):
        """FHIR Appointment resource maps to internal slot dict."""
        from app.ehr.fhir_mapper import FHIRMapper

        mapper = FHIRMapper()
        fhir_appt = {
            "resourceType": "Appointment",
            "id": "APT001",
            "status": "booked",
            "start": "2026-07-01T09:00:00Z",
            "participant": [{"actor": {"reference": "Practitioner/P001"}}],
        }

        internal = mapper.fhir_appointment_to_internal(fhir_appt)

        assert internal["appointment_id"] == "APT001"
        assert internal["status"] == "confirmed"
        assert "datetime" in internal
