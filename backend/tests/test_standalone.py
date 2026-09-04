"""
Carenova Standalone Mode — Complete Test Suite
TDD RED phase — every feature of the world's best standalone clinic system.

What standalone mode is:
  Carenova IS the EHR. No external system needed.
  Works for:
    - Nigerian hospitals on pen and paper
    - New US practices that haven't chosen an EHR yet
    - Rural clinics globally with no connectivity for heavy systems
    - Dental, physio, mental health practices that never adopt full EHR
    - Any clinic that tried an EHR, hated it, and went back to paper
    - Excel-based clinics wanting their first real system

What makes it the best globally:
  1. Works on WhatsApp + 2G (no app download, no computer needed)
  2. AI answers calls AND manages WhatsApp simultaneously
  3. Supabase as the record store — HIPAA + NDPR + GDPR compliant
  4. Built-in patient records, appointments, vitals, medications, visits
  5. Multi-language (English, Igbo, Yoruba, Hausa, French, Swahili)
  6. Works offline-first — syncs when internet returns
  7. CSV/Excel import — migrate from paper and spreadsheets instantly
  8. WhatsApp-to-record: nurse sends a message, patient is created
  9. Pre-visit note pre-population from intake data (scribe lite)
 10. Upgrade path — connect an EHR later without losing any data
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, date


# ── 1. Standalone clinic mode detection ──────────────────────────────────────

class TestStandaloneMode:

    def test_standalone_mode_can_be_imported(self):
        from app.standalone.manager import StandaloneManager
        assert StandaloneManager is not None

    def test_standalone_manager_initialises_with_clinic_id(self):
        from app.standalone.manager import StandaloneManager
        mgr = StandaloneManager(clinic_id="clinic_001")
        assert mgr.clinic_id == "clinic_001"

    def test_ehr_mode_is_none_in_standalone(self):
        from app.standalone.manager import StandaloneManager
        mgr = StandaloneManager(clinic_id="clinic_001")
        assert mgr.ehr_type == "standalone"

    def test_standalone_flag_in_clinic_model(self):
        """Clinic model must support standalone mode flag."""
        from app.models.clinic import Clinic
        # ehr_type = "standalone" is valid
        clinic = Clinic()
        clinic.ehr_type = "standalone"
        assert clinic.ehr_type == "standalone"

    def test_standalone_clinic_can_operate_without_ehr_credentials(self):
        """A standalone clinic has no ehr_practice_id — that is valid."""
        from app.standalone.manager import StandaloneManager
        mgr = StandaloneManager(clinic_id="clinic_ng_001")
        assert mgr.requires_ehr_credentials() is False


# ── 2. Patient record management (Supabase as EHR) ───────────────────────────

class TestStandalonePatientRecords:

    @pytest.mark.asyncio
    async def test_create_patient_stores_in_supabase(self):
        """Patient created in Supabase — no external EHR call."""
        from app.standalone.patients import StandalonePatientService

        svc = StandalonePatientService(clinic_id="clinic_001")

        with patch.object(svc, "_save_to_db", return_value={
            "id": "PAT-NG-001",
            "first_name": "Amaka",
            "last_name": "Obi",
            "phone": "+2348031234567",
            "clinic_id": "clinic_001",
        }) as mock_save:
            result = await svc.create_patient({
                "first_name": "Amaka",
                "last_name": "Obi",
                "phone": "+2348031234567",
                "date_of_birth": "1990-03-15",
                "gender": "female",
            })

        assert result["patient_id"] == "PAT-NG-001"
        assert result["first_name"] == "Amaka"

    @pytest.mark.asyncio
    async def test_search_patient_by_phone(self):
        from app.standalone.patients import StandalonePatientService

        svc = StandalonePatientService(clinic_id="clinic_001")

        with patch.object(svc, "_query_db", return_value=[{
            "id": "PAT-NG-001",
            "first_name": "Amaka",
            "last_name": "Obi",
            "phone": "+2348031234567",
        }]):
            result = await svc.find_patient_by_phone("+2348031234567")

        assert result is not None
        assert result["patient_id"] == "PAT-NG-001"

    @pytest.mark.asyncio
    async def test_search_patient_not_found_returns_none(self):
        from app.standalone.patients import StandalonePatientService

        svc = StandalonePatientService(clinic_id="clinic_001")

        with patch.object(svc, "_query_db", return_value=[]):
            result = await svc.find_patient_by_phone("+2340000000000")

        assert result is None

    @pytest.mark.asyncio
    async def test_update_patient_record(self):
        from app.standalone.patients import StandalonePatientService

        svc = StandalonePatientService(clinic_id="clinic_001")

        with patch.object(svc, "_update_db", return_value={
            "id": "PAT-NG-001", "email": "amaka@example.com"
        }):
            result = await svc.update_patient(
                patient_id="PAT-NG-001",
                data={"email": "amaka@example.com"},
            )

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_patient_visit_history(self):
        """Full visit history stored in Supabase — no EHR needed."""
        from app.standalone.patients import StandalonePatientService

        svc = StandalonePatientService(clinic_id="clinic_001")

        with patch.object(svc, "_query_db", return_value=[
            {"id": "VISIT-001", "date": "2026-05-01", "reason": "Annual exam",
             "provider": "Dr. Chukwu", "notes": "Patient stable"},
            {"id": "VISIT-002", "date": "2026-06-15", "reason": "Follow-up",
             "provider": "Dr. Chukwu", "notes": "BP improved"},
        ]):
            history = await svc.get_visit_history(patient_id="PAT-NG-001")

        assert len(history) == 2
        assert history[0]["reason"] == "Annual exam"


# ── 3. WhatsApp-to-record (nurse sends message → patient created) ─────────────

class TestWhatsAppToRecord:

    @pytest.mark.asyncio
    async def test_nurse_whatsapp_message_creates_patient(self):
        """
        Nurse sends WhatsApp message in natural language.
        Carenova parses it and creates the patient record.
        No computer required. Works on any phone.

        Input: "New patient: Amaka Obi, female, DOB 15 March 1990,
                phone 08031234567"
        """
        from app.standalone.whatsapp_intake import WhatsAppIntakeParser

        parser = WhatsAppIntakeParser()
        result = await parser.parse_nurse_message(
            "New patient: Amaka Obi, female, DOB 15 March 1990, phone 08031234567"
        )

        assert result["first_name"] == "Amaka"
        assert result["last_name"] == "Obi"
        assert result["gender"] == "female"
        assert result["date_of_birth"] == "1990-03-15"
        assert "08031234567" in result["phone"]

    @pytest.mark.asyncio
    async def test_parser_handles_igbo_name_formats(self):
        """Nigerian names — handles Igbo naming patterns correctly."""
        from app.standalone.whatsapp_intake import WhatsAppIntakeParser

        parser = WhatsAppIntakeParser()
        result = await parser.parse_nurse_message(
            "Patient: Chukwuemeka Nwosu, male, 45 years old, 07012345678"
        )

        assert result["first_name"] == "Chukwuemeka"
        assert result["last_name"] == "Nwosu"
        assert result["gender"] == "male"

    @pytest.mark.asyncio
    async def test_parser_handles_appointment_booking_message(self):
        """
        Nurse books appointment via WhatsApp message.
        Input: "Book Amaka Obi 08031234567 for Dr. Chukwu tomorrow 10am"
        """
        from app.standalone.whatsapp_intake import WhatsAppIntakeParser

        parser = WhatsAppIntakeParser()
        result = await parser.parse_nurse_message(
            "Book Amaka Obi 08031234567 for Dr. Chukwu tomorrow 10am"
        )

        assert result["intent"] == "book_appointment"
        assert "Amaka" in result["patient_name"]
        assert "Chukwu" in result["provider_name"]
        assert result["time"] == "10:00"

    @pytest.mark.asyncio
    async def test_parser_handles_vitals_recording(self):
        """
        Nurse records vitals via WhatsApp.
        Input: "Vitals PAT-001: BP 120/80, temp 37.2, pulse 72"
        """
        from app.standalone.whatsapp_intake import WhatsAppIntakeParser

        parser = WhatsAppIntakeParser()
        result = await parser.parse_nurse_message(
            "Vitals PAT-NG-001: BP 120/80, temp 37.2, pulse 72"
        )

        assert result["intent"] == "record_vitals"
        assert result["blood_pressure"] == "120/80"
        assert result["temperature"] == "37.2"
        assert result["pulse"] == "72"

    @pytest.mark.asyncio
    async def test_parser_handles_french_input(self):
        """French language support — Francophone Africa."""
        from app.standalone.whatsapp_intake import WhatsAppIntakeParser

        parser = WhatsAppIntakeParser()
        result = await parser.parse_nurse_message(
            "Nouveau patient: Marie Dupont, femme, née le 10 mars 1985, téléphone 0701234567"
        )

        assert result["first_name"] == "Marie"
        assert result["last_name"] == "Dupont"
        assert result["language_detected"] == "fr"


# ── 4. Standalone appointment management ─────────────────────────────────────

class TestStandaloneAppointments:

    @pytest.mark.asyncio
    async def test_get_available_slots_from_provider_schedule(self):
        """
        Slots come from Carenova's own schedule — not an external EHR.
        Each provider has a configured schedule in Supabase.
        """
        from app.standalone.scheduling import StandaloneScheduler

        scheduler = StandaloneScheduler(clinic_id="clinic_001")

        with patch.object(scheduler, "_get_provider_schedule", return_value={
            "provider_id": "PROV-001",
            "name": "Dr. Chukwu",
            "working_hours": {"mon": "09:00-17:00", "tue": "09:00-17:00",
                              "wed": "09:00-17:00", "thu": "09:00-17:00",
                              "fri": "09:00-14:00"},
            "slot_duration_minutes": 20,
            "break_times": ["13:00-14:00"],
        }):
            with patch.object(scheduler, "_get_booked_slots", return_value=[
                "2026-07-01T10:00:00", "2026-07-01T10:20:00"
            ]):
                slots = await scheduler.get_available_slots(
                    provider_id="PROV-001",
                    date="2026-07-01",
                )

        assert len(slots) > 0
        assert all(s["status"] == "free" for s in slots)
        # Booked slots should not appear
        slot_times = [s["datetime_iso"] for s in slots]
        assert "2026-07-01T10:00:00" not in slot_times

    @pytest.mark.asyncio
    async def test_book_appointment_stores_in_supabase(self):
        from app.standalone.scheduling import StandaloneScheduler

        scheduler = StandaloneScheduler(clinic_id="clinic_001")

        with patch.object(scheduler, "_save_appointment", return_value={
            "id": "APT-NG-001",
            "patient_id": "PAT-NG-001",
            "provider_id": "PROV-001",
            "datetime": "2026-07-01T09:00:00",
            "status": "confirmed",
        }):
            result = await scheduler.book_appointment(
                patient_id="PAT-NG-001",
                provider_id="PROV-001",
                datetime_iso="2026-07-01T09:00:00",
                reason="Annual checkup",
                duration_minutes=20,
            )

        assert result["appointment_id"] == "APT-NG-001"
        assert result["status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_appointment_sends_whatsapp_confirmation(self):
        """
        After booking, patient receives WhatsApp confirmation automatically.
        No staff action required.
        """
        from app.standalone.scheduling import StandaloneScheduler

        scheduler = StandaloneScheduler(clinic_id="clinic_001")

        confirmation_sent = []

        async def capture_whatsapp(phone, message):
            confirmation_sent.append({"phone": phone, "message": message})

        with patch.object(scheduler, "_save_appointment", return_value={
            "id": "APT-NG-001", "status": "confirmed",
            "datetime": "2026-07-01T09:00:00"
        }):
            with patch.object(scheduler, "_send_whatsapp_confirmation",
                               side_effect=capture_whatsapp):
                await scheduler.book_appointment(
                    patient_id="PAT-NG-001",
                    patient_phone="+2348031234567",
                    provider_id="PROV-001",
                    datetime_iso="2026-07-01T09:00:00",
                    reason="Annual checkup",
                    duration_minutes=20,
                )

        assert len(confirmation_sent) == 1
        assert "+2348031234567" in confirmation_sent[0]["phone"]

    @pytest.mark.asyncio
    async def test_appointment_reminder_sent_24h_before(self):
        """Reminder sent 24 hours before appointment via WhatsApp."""
        from app.standalone.scheduling import StandaloneScheduler

        scheduler = StandaloneScheduler(clinic_id="clinic_001")
        reminders = []

        with patch.object(scheduler, "_queue_reminder",
                           side_effect=lambda **kw: reminders.append(kw)):
            await scheduler.schedule_reminder(
                appointment_id="APT-NG-001",
                patient_phone="+2348031234567",
                appointment_datetime="2026-07-02T09:00:00",
                hours_before=24,
            )

        assert len(reminders) == 1
        assert reminders[0]["hours_before"] == 24


# ── 5. Provider schedule management ──────────────────────────────────────────

class TestProviderScheduleManagement:

    @pytest.mark.asyncio
    async def test_create_provider_schedule(self):
        """
        Clinic admin sets up provider working hours.
        Carenova uses this to generate slots.
        """
        from app.standalone.providers import StandaloneProviderService

        svc = StandaloneProviderService(clinic_id="clinic_001")

        with patch.object(svc, "_save_provider", return_value={
            "id": "PROV-001",
            "name": "Dr. Chukwu Emeka",
            "specialty": "Family Medicine",
            "clinic_id": "clinic_001",
        }):
            result = await svc.create_provider({
                "name": "Dr. Chukwu Emeka",
                "specialty": "Family Medicine",
                "working_hours": {
                    "mon": "09:00-17:00",
                    "tue": "09:00-17:00",
                    "wed": "09:00-17:00",
                    "thu": "09:00-17:00",
                    "fri": "09:00-14:00",
                },
                "slot_duration_minutes": 20,
            })

        assert result["provider_id"] == "PROV-001"
        assert result["name"] == "Dr. Chukwu Emeka"

    @pytest.mark.asyncio
    async def test_get_all_providers_for_clinic(self):
        from app.standalone.providers import StandaloneProviderService

        svc = StandaloneProviderService(clinic_id="clinic_001")

        with patch.object(svc, "_query_providers", return_value=[
            {"id": "PROV-001", "name": "Dr. Chukwu Emeka", "specialty": "Family Medicine"},
            {"id": "PROV-002", "name": "Dr. Ngozi Adeyemi", "specialty": "Pediatrics"},
        ]):
            providers = await svc.get_all_providers()

        assert len(providers) == 2
        assert providers[0]["name"] == "Dr. Chukwu Emeka"


# ── 6. Vitals and clinical notes ─────────────────────────────────────────────

class TestVitalsAndClinicalNotes:

    @pytest.mark.asyncio
    async def test_record_vitals_for_patient(self):
        """
        Nurse records vitals — stored in Supabase.
        This is the scribe-lite feature.
        """
        from app.standalone.clinical import StandaloneClinicalService

        svc = StandaloneClinicalService(clinic_id="clinic_001")

        with patch.object(svc, "_save_vitals", return_value={
            "id": "VITAL-001",
            "patient_id": "PAT-NG-001",
            "recorded_at": "2026-07-01T09:15:00",
            "blood_pressure": "120/80",
            "temperature_celsius": 37.2,
            "pulse_bpm": 72,
            "weight_kg": 65.0,
            "height_cm": 165.0,
        }):
            result = await svc.record_vitals(
                patient_id="PAT-NG-001",
                appointment_id="APT-NG-001",
                vitals={
                    "blood_pressure": "120/80",
                    "temperature_celsius": 37.2,
                    "pulse_bpm": 72,
                    "weight_kg": 65.0,
                    "height_cm": 165.0,
                },
            )

        assert result["blood_pressure"] == "120/80"
        assert result["temperature_celsius"] == 37.2

    @pytest.mark.asyncio
    async def test_pre_visit_note_prepopulated_from_intake(self):
        """
        Scribe-lite: intake data from the call prepopulates a draft note.
        Physician opens a partially completed note — not a blank screen.
        """
        from app.standalone.clinical import StandaloneClinicalService

        svc = StandaloneClinicalService(clinic_id="clinic_001")

        intake_data = {
            "chief_complaint": "Persistent cough for 2 weeks",
            "current_medications": ["Amoxicillin 500mg", "Vitamin C"],
            "allergies": ["Penicillin"],
            "last_visit_reason": "Annual physical",
        }

        note = await svc.generate_pre_visit_note(
            patient_id="PAT-NG-001",
            appointment_id="APT-NG-001",
            intake_data=intake_data,
        )

        assert note is not None
        assert "chief_complaint" in note
        assert note["chief_complaint"] == "Persistent cough for 2 weeks"
        assert "Penicillin" in note["allergies"]
        assert note["status"] == "draft"

    @pytest.mark.asyncio
    async def test_save_clinical_note(self):
        from app.standalone.clinical import StandaloneClinicalService

        svc = StandaloneClinicalService(clinic_id="clinic_001")

        with patch.object(svc, "_save_note", return_value={
            "id": "NOTE-001",
            "patient_id": "PAT-NG-001",
            "soap_subjective": "Patient presents with persistent cough",
            "soap_objective": "BP 120/80, Temp 37.2",
            "soap_assessment": "Upper respiratory infection",
            "soap_plan": "Amoxicillin 500mg TID x 7 days",
            "status": "final",
        }):
            result = await svc.save_clinical_note(
                patient_id="PAT-NG-001",
                appointment_id="APT-NG-001",
                note={
                    "soap_subjective": "Patient presents with persistent cough",
                    "soap_objective": "BP 120/80, Temp 37.2",
                    "soap_assessment": "Upper respiratory infection",
                    "soap_plan": "Amoxicillin 500mg TID x 7 days",
                },
            )

        assert result["status"] == "final"
        assert "Amoxicillin" in result["soap_plan"]


# ── 7. CSV / Excel import ─────────────────────────────────────────────────────

class TestDataImport:

    @pytest.mark.asyncio
    async def test_import_patients_from_csv(self):
        """
        Migrate from Excel/paper to Carenova in one step.
        Nurse exports Excel as CSV, uploads, patients are created.
        """
        from app.standalone.importer import StandaloneDataImporter

        importer = StandaloneDataImporter(clinic_id="clinic_001")

        csv_content = """first_name,last_name,phone,date_of_birth,gender
Amaka,Obi,08031234567,1990-03-15,female
Chukwu,Nwosu,07012345678,1985-11-22,male
Ngozi,Adeyemi,08098765432,1975-07-04,female"""

        with patch.object(importer, "_bulk_save_patients", return_value={
            "created": 3, "skipped": 0, "errors": []
        }):
            result = await importer.import_patients_csv(csv_content)

        assert result["created"] == 3
        assert result["skipped"] == 0
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_import_handles_duplicate_phone_numbers(self):
        """Duplicate phone numbers are skipped — not created twice."""
        from app.standalone.importer import StandaloneDataImporter

        importer = StandaloneDataImporter(clinic_id="clinic_001")

        csv_content = """first_name,last_name,phone,date_of_birth,gender
Amaka,Obi,08031234567,1990-03-15,female
Amaka,Obi,08031234567,1990-03-15,female"""

        with patch.object(importer, "_bulk_save_patients", return_value={
            "created": 1, "skipped": 1, "errors": []
        }):
            result = await importer.import_patients_csv(csv_content)

        assert result["created"] == 1
        assert result["skipped"] == 1

    @pytest.mark.asyncio
    async def test_import_handles_missing_optional_fields(self):
        """Import works even if DOB or email is missing."""
        from app.standalone.importer import StandaloneDataImporter

        importer = StandaloneDataImporter(clinic_id="clinic_001")

        csv_content = """first_name,last_name,phone
Amaka,Obi,08031234567"""

        with patch.object(importer, "_bulk_save_patients", return_value={
            "created": 1, "skipped": 0, "errors": []
        }):
            result = await importer.import_patients_csv(csv_content)

        assert result["created"] == 1


# ── 8. Offline-first sync ─────────────────────────────────────────────────────

class TestOfflineSync:

    def test_offline_queue_exists(self):
        """Operations queued when offline, synced when internet returns."""
        from app.standalone.sync import OfflineSyncQueue
        queue = OfflineSyncQueue(clinic_id="clinic_001")
        assert queue is not None

    @pytest.mark.asyncio
    async def test_operations_queued_when_db_unreachable(self):
        from app.standalone.sync import OfflineSyncQueue

        queue = OfflineSyncQueue(clinic_id="clinic_001")

        await queue.enqueue({
            "operation": "create_patient",
            "data": {"first_name": "Amaka", "last_name": "Obi", "phone": "+2348031234567"},
            "timestamp": "2026-07-01T09:00:00",
        })

        pending = await queue.get_pending()
        assert len(pending) == 1
        assert pending[0]["operation"] == "create_patient"

    @pytest.mark.asyncio
    async def test_queue_cleared_after_successful_sync(self):
        from app.standalone.sync import OfflineSyncQueue

        queue = OfflineSyncQueue(clinic_id="clinic_001")
        await queue.enqueue({
            "operation": "create_patient",
            "data": {"first_name": "Amaka"},
            "timestamp": "2026-07-01T09:00:00",
        })

        with patch.object(queue, "_sync_to_db", return_value=True):
            await queue.sync_all()

        pending = await queue.get_pending()
        assert len(pending) == 0


# ── 9. EHR upgrade path ───────────────────────────────────────────────────────

class TestEHRUpgradePath:

    @pytest.mark.asyncio
    async def test_standalone_clinic_can_upgrade_to_ehr(self):
        """
        A standalone clinic can connect an EHR later.
        All Carenova data preserved — nothing lost during upgrade.
        """
        from app.standalone.manager import StandaloneManager

        mgr = StandaloneManager(clinic_id="clinic_001")
        assert mgr.ehr_type == "standalone"

        with patch.object(mgr, "_update_clinic_ehr_type"):
            with patch.object(mgr, "_export_patients_to_ehr", return_value={"migrated": 47}):
                result = await mgr.upgrade_to_ehr(
                    ehr_type="athenahealth",
                    credentials={
                        "client_id": "test_id",
                        "client_secret": "test_secret",
                        "practice_id": "195900",
                    },
                )

        assert result["migrated_patients"] == 47
        assert result["new_ehr_type"] == "athenahealth"

    @pytest.mark.asyncio
    async def test_upgrade_preserves_all_historical_data(self):
        """All visits, vitals, notes stay in Carenova after EHR upgrade."""
        from app.standalone.manager import StandaloneManager

        mgr = StandaloneManager(clinic_id="clinic_001")

        with patch.object(mgr, "_update_clinic_ehr_type"):
            with patch.object(mgr, "_export_patients_to_ehr",
                               return_value={"migrated": 47}):
                result = await mgr.upgrade_to_ehr(
                    ehr_type="modmed",
                    credentials={
                        "client_id": "id", "client_secret": "s",
                        "practice_prefix": "myhospital", "api_key": "key"
                    },
                )

        # Historical Carenova data always preserved
        assert result.get("historical_data_preserved") is True


# ── 10. Multi-language support ────────────────────────────────────────────────

class TestMultiLanguageSupport:

    @pytest.mark.asyncio
    async def test_whatsapp_confirmation_in_english(self):
        from app.standalone.messaging import StandaloneMessaging
        msg = StandaloneMessaging()
        text = await msg.appointment_confirmation(
            patient_name="Amaka Obi",
            provider_name="Dr. Chukwu",
            datetime_str="Tuesday July 1 at 9:00 AM",
            clinic_name="Owerri Family Clinic",
            language="en",
        )
        assert "Amaka" in text
        assert "Dr. Chukwu" in text
        assert "9:00 AM" in text

    @pytest.mark.asyncio
    async def test_whatsapp_confirmation_in_igbo(self):
        from app.standalone.messaging import StandaloneMessaging
        msg = StandaloneMessaging()
        text = await msg.appointment_confirmation(
            patient_name="Amaka Obi",
            provider_name="Dr. Chukwu",
            datetime_str="Tuesday July 1 at 9:00 AM",
            clinic_name="Owerri Family Clinic",
            language="ig",
        )
        assert "Amaka" in text
        assert len(text) > 20

    @pytest.mark.asyncio
    async def test_whatsapp_confirmation_in_yoruba(self):
        from app.standalone.messaging import StandaloneMessaging
        msg = StandaloneMessaging()
        text = await msg.appointment_confirmation(
            patient_name="Ngozi Adeyemi",
            provider_name="Dr. Bello",
            datetime_str="Wednesday July 2 at 10:00 AM",
            clinic_name="Lagos Clinic",
            language="yo",
        )
        assert "Ngozi" in text

    @pytest.mark.asyncio
    async def test_whatsapp_confirmation_in_french(self):
        from app.standalone.messaging import StandaloneMessaging
        msg = StandaloneMessaging()
        text = await msg.appointment_confirmation(
            patient_name="Marie Dupont",
            provider_name="Dr. Kone",
            datetime_str="Jeudi 3 Juillet à 9h00",
            clinic_name="Clinique Abidjan",
            language="fr",
        )
        assert "Marie" in text


# ── 11. Global pricing ────────────────────────────────────────────────────────

class TestGlobalStandalonePricing:

    def test_nigeria_pricing_in_naira(self):
        from app.standalone.pricing import StandalonePricing
        price = StandalonePricing.get_price(country="NG", tier="starter")
        assert price["currency"] == "NGN"
        assert price["amount"] == 25_000
        assert price["payment_provider"] == "paystack"

    def test_us_pricing_in_usd(self):
        from app.standalone.pricing import StandalonePricing
        price = StandalonePricing.get_price(country="US", tier="pro")
        assert price["currency"] == "USD"
        assert price["amount"] == 999
        assert price["payment_provider"] in ("lemonsqueezy", "stripe")

    def test_kenya_pricing_in_kes(self):
        from app.standalone.pricing import StandalonePricing
        price = StandalonePricing.get_price(country="KE", tier="starter")
        assert price["currency"] == "KES"
        assert price["amount"] > 0

    def test_philippines_pricing_in_php(self):
        from app.standalone.pricing import StandalonePricing
        price = StandalonePricing.get_price(country="PH", tier="starter")
        assert price["currency"] == "PHP"
        assert price["amount"] > 0

    def test_uk_pricing_in_gbp(self):
        from app.standalone.pricing import StandalonePricing
        price = StandalonePricing.get_price(country="GB", tier="pro")
        assert price["currency"] == "GBP"
        assert price["amount"] > 0

    def test_unknown_country_defaults_to_usd(self):
        from app.standalone.pricing import StandalonePricing
        price = StandalonePricing.get_price(country="XX", tier="starter")
        assert price["currency"] == "USD"
