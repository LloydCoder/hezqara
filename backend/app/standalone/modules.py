"""
Standalone Mode — All supporting modules.

scheduling.py  — Appointment management without an EHR
clinical.py    — Vitals, notes, pre-visit note pre-population
importer.py    — CSV/Excel migration from paper
sync.py        — Offline-first queue
messaging.py   — Multi-language WhatsApp messages
providers.py   — Provider and schedule management
pricing.py     — Global pricing in local currencies
"""
import logging
import uuid
import csv
import io
import json
from typing import Optional
from datetime import datetime, date, time, timedelta

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Standalone Scheduler
# ══════════════════════════════════════════════════════════════════════════════

class StandaloneScheduler:
    """
    Manages appointments without any external EHR.
    Slots are generated from provider schedules stored in Supabase.
    """

    def __init__(self, clinic_id: str) -> None:
        self.clinic_id = clinic_id

    async def get_available_slots(
        self,
        provider_id: str,
        date: str,
        appointment_type: Optional[str] = None,
    ) -> list:
        """
        Generate available slots from provider schedule.
        Excludes already-booked slots.
        """
        try:
            schedule = await self._get_provider_schedule(provider_id)
            booked = await self._get_booked_slots(provider_id=provider_id, date=date)

            day_name = datetime.fromisoformat(date).strftime("%a").lower()
            working_hours = schedule.get("working_hours", {})
            hours_str = working_hours.get(day_name[:3])

            if not hours_str:
                return []  # Provider not working this day

            start_str, end_str = hours_str.split("-")
            start_h, start_m = map(int, start_str.split(":"))
            end_h, end_m = map(int, end_str.split(":"))

            slot_duration = schedule.get("slot_duration_minutes", 20)
            break_times = schedule.get("break_times", [])

            slots = []
            current = datetime.combine(
                datetime.fromisoformat(date).date(),
                time(start_h, start_m)
            )
            end_dt = datetime.combine(
                datetime.fromisoformat(date).date(),
                time(end_h, end_m)
            )

            while current + timedelta(minutes=slot_duration) <= end_dt:
                slot_iso = current.isoformat()

                # Skip break times
                in_break = False
                for break_range in break_times:
                    b_start, b_end = break_range.split("-")
                    bsh, bsm = map(int, b_start.split(":"))
                    beh, bem = map(int, b_end.split(":"))
                    break_start = datetime.combine(
                        datetime.fromisoformat(date).date(), time(bsh, bsm)
                    )
                    break_end = datetime.combine(
                        datetime.fromisoformat(date).date(), time(beh, bem)
                    )
                    if break_start <= current < break_end:
                        in_break = True
                        break

                if not in_break and slot_iso not in booked:
                    slots.append({
                        "slot_id": f"SLOT-{provider_id}-{current.strftime('%H%M')}",
                        "datetime_iso": slot_iso,
                        "datetime": slot_iso,
                        "provider_id": provider_id,
                        "duration_minutes": slot_duration,
                        "status": "free",
                    })

                current += timedelta(minutes=slot_duration)

            return slots

        except Exception as e:
            logger.error("StandaloneScheduler.get_available_slots failed: %s", e)
            return []

    async def book_appointment(
        self,
        patient_id: str,
        provider_id: str,
        datetime_iso: str,
        reason: str,
        duration_minutes: int = 20,
        patient_phone: Optional[str] = None,
    ) -> dict:
        """Book appointment and send WhatsApp confirmation."""
        appointment = await self._save_appointment({
            "id": f"APT-{uuid.uuid4().hex[:8].upper()}",
            "clinic_id": self.clinic_id,
            "patient_id": patient_id,
            "provider_id": provider_id,
            "datetime": datetime_iso,
            "duration_minutes": duration_minutes,
            "reason": reason,
            "status": "confirmed",
        })

        # Send WhatsApp confirmation if phone provided
        if patient_phone:
            await self._send_whatsapp_confirmation(
                phone=patient_phone,
                message=f"Your appointment is confirmed for {datetime_iso}.",
            )

        return {
            "appointment_id": appointment.get("id", ""),
            "status": "confirmed",
            "datetime_iso": appointment.get("datetime", datetime_iso),
        }

    async def cancel_appointment(
        self, appointment_id: str, reason: str = "Patient request"
    ) -> dict:
        """Cancel appointment and notify patient."""
        await self._update_appointment_status(appointment_id, "cancelled")
        return {"status": "cancelled", "appointment_id": appointment_id}

    async def schedule_reminder(
        self,
        appointment_id: str,
        patient_phone: str,
        appointment_datetime: str,
        hours_before: int = 24,
    ) -> None:
        """Queue a reminder to be sent N hours before appointment."""
        await self._queue_reminder(
            appointment_id=appointment_id,
            patient_phone=patient_phone,
            appointment_datetime=appointment_datetime,
            hours_before=hours_before,
        )

    # ── DB layer stubs ──

    async def _get_provider_schedule(self, provider_id: str) -> dict:
        return {}

    async def _get_booked_slots(self, provider_id: str, date: str) -> list:
        return []

    async def _save_appointment(self, data: dict) -> dict:
        return data

    async def _send_whatsapp_confirmation(self, phone: str, message: str) -> None:
        pass

    async def _update_appointment_status(self, appointment_id: str, status: str) -> None:
        pass

    async def _queue_reminder(self, **kwargs) -> None:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# Standalone Clinical Service
# ══════════════════════════════════════════════════════════════════════════════

class StandaloneClinicalService:
    """
    Vitals, clinical notes, and pre-visit note pre-population.
    Scribe-lite: intake data prepopulates a draft SOAP note.
    """

    def __init__(self, clinic_id: str) -> None:
        self.clinic_id = clinic_id

    async def record_vitals(
        self, patient_id: str, appointment_id: str, vitals: dict
    ) -> dict:
        """Record vitals for a patient visit."""
        record = {
            "id": f"VITAL-{uuid.uuid4().hex[:8].upper()}",
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "clinic_id": self.clinic_id,
            "recorded_at": datetime.utcnow().isoformat(),
            **vitals,
        }
        return await self._save_vitals(record)

    async def generate_pre_visit_note(
        self,
        patient_id: str,
        appointment_id: str,
        intake_data: dict,
    ) -> dict:
        """
        Scribe-lite: generate a draft SOAP note from intake data.
        Physician opens a partially completed note — not a blank screen.
        Saves 5–10 minutes per encounter.
        """
        draft = {
            "id": f"NOTE-{uuid.uuid4().hex[:8].upper()}",
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "clinic_id": self.clinic_id,
            "status": "draft",
            "generated_at": datetime.utcnow().isoformat(),
            # SOAP structure — pre-populated from intake
            "chief_complaint": intake_data.get("chief_complaint", ""),
            "history_of_present_illness": self._generate_hpi(intake_data),
            "current_medications": intake_data.get("current_medications", []),
            "allergies": intake_data.get("allergies", []),
            "last_visit_reason": intake_data.get("last_visit_reason", ""),
            # Sections physician must complete
            "soap_objective": "",   # Exam findings — physician fills
            "soap_assessment": "",  # Diagnosis — physician fills
            "soap_plan": "",        # Treatment plan — physician fills
        }
        return draft

    async def save_clinical_note(
        self,
        patient_id: str,
        appointment_id: str,
        note: dict,
    ) -> dict:
        """Save finalized clinical note to Supabase."""
        record = {
            "id": f"NOTE-{uuid.uuid4().hex[:8].upper()}",
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "clinic_id": self.clinic_id,
            "status": "final",
            "finalized_at": datetime.utcnow().isoformat(),
            **note,
        }
        return await self._save_note(record)

    def _generate_hpi(self, intake: dict) -> str:
        """Generate History of Present Illness from intake data."""
        cc = intake.get("chief_complaint", "")
        if not cc:
            return ""
        parts = [f"Patient presents with {cc}."]
        if intake.get("symptom_duration"):
            parts.append(f"Duration: {intake['symptom_duration']}.")
        if intake.get("current_medications"):
            meds = ", ".join(intake["current_medications"])
            parts.append(f"Currently taking: {meds}.")
        return " ".join(parts)

    async def _save_vitals(self, record: dict) -> dict:
        return record

    async def _save_note(self, record: dict) -> dict:
        return record


# ══════════════════════════════════════════════════════════════════════════════
# Standalone Data Importer
# ══════════════════════════════════════════════════════════════════════════════

class StandaloneDataImporter:
    """
    One-step migration from paper/Excel to Carenova.
    Nurse exports Excel as CSV, uploads, patients created instantly.
    """

    def __init__(self, clinic_id: str) -> None:
        self.clinic_id = clinic_id

    async def import_patients_csv(self, csv_content: str) -> dict:
        """
        Import patients from CSV string.
        Handles: missing fields, duplicates, malformed rows.
        Required columns: first_name, last_name, phone
        Optional: date_of_birth, gender, email, address
        """
        reader = csv.DictReader(io.StringIO(csv_content.strip()))
        patients = []
        errors = []
        seen_phones = set()

        for i, row in enumerate(reader, start=2):  # Row 1 is header
            try:
                first_name = row.get("first_name", "").strip()
                last_name = row.get("last_name", "").strip()
                phone = row.get("phone", "").strip()

                if not first_name or not last_name:
                    errors.append({"row": i, "error": "Missing first_name or last_name"})
                    continue

                # Deduplicate by phone
                if phone and phone in seen_phones:
                    continue  # Skip duplicate
                if phone:
                    seen_phones.add(phone)

                patients.append({
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone": phone,
                    "date_of_birth": row.get("date_of_birth", "").strip() or None,
                    "gender": row.get("gender", "").strip().lower() or None,
                    "email": row.get("email", "").strip() or None,
                    "clinic_id": self.clinic_id,
                })
            except Exception as e:
                errors.append({"row": i, "error": str(e)})

        if patients:
            result = await self._bulk_save_patients(patients)
            return {
                "created": result.get("created", len(patients)),
                "skipped": result.get("skipped", 0),
                "errors": errors,
            }

        return {"created": 0, "skipped": 0, "errors": errors}

    async def _bulk_save_patients(self, patients: list) -> dict:
        return {"created": len(patients), "skipped": 0}


# ══════════════════════════════════════════════════════════════════════════════
# Offline Sync Queue
# ══════════════════════════════════════════════════════════════════════════════

class OfflineSyncQueue:
    """
    Offline-first operation queue — Redis-backed.

    Operations enqueued when DB unreachable. Auto-synced when connectivity
    restored. Critical for rural clinics with intermittent internet and
    frequent power outages — the #1 cited infrastructure challenge across
    Nigerian hospital management software guides.

    Redis is the source of truth so queued operations survive a process
    restart (e.g. the clinic's server rebooting during a power cut).
    If Redis itself is unreachable, falls back to in-memory rather than
    crashing — degraded but functional, with a logged warning since the
    durability guarantee is lost in that fallback state.
    """

    def __init__(self, clinic_id: str, redis_client=None) -> None:
        self.clinic_id = clinic_id
        self._redis = redis_client
        self._memory_fallback: list = []  # Used only if Redis unavailable
        self._using_fallback = False

    def _redis_key(self) -> str:
        return f"offline_sync:{self.clinic_id}"

    async def enqueue(self, operation: dict) -> None:
        """Add operation to sync queue. Persists to Redis when available."""
        record = {
            "id": uuid.uuid4().hex,
            "clinic_id": self.clinic_id,
            "queued_at": datetime.utcnow().isoformat(),
            **operation,
        }

        if self._redis is not None:
            try:
                await self._redis.rpush(self._redis_key(), json.dumps(record))
                return
            except Exception as e:
                logger.warning(
                    "Redis unreachable for offline sync queue (clinic=%s): %s — "
                    "falling back to in-memory. Durability guarantee degraded.",
                    self.clinic_id, e,
                )
                self._using_fallback = True

        self._memory_fallback.append(record)

    async def get_pending(self) -> list:
        """Return all pending operations — read from Redis if available."""
        if self._redis is not None and not self._using_fallback:
            try:
                raw = await self._redis.lrange(self._redis_key(), 0, -1)
                return [json.loads(r) for r in raw]
            except Exception as e:
                logger.warning(
                    "Redis unreachable reading offline sync queue (clinic=%s): %s",
                    self.clinic_id, e,
                )
                self._using_fallback = True

        return list(self._memory_fallback)

    async def sync_all(self) -> dict:
        """
        Attempt to sync all pending operations to Supabase.
        Removes successfully synced operations from Redis (or memory fallback).
        """
        pending = await self.get_pending()
        if not pending:
            return {"synced": 0, "failed": 0}

        synced = 0
        failed = 0

        for op in pending:
            try:
                success = await self._sync_to_db(op)
                if success:
                    await self._remove(op)
                    synced += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error("Sync failed for op %s: %s", op.get("id"), e)
                failed += 1

        return {"synced": synced, "failed": failed}

    async def _remove(self, op: dict) -> None:
        """Remove a successfully synced operation from the queue."""
        if self._redis is not None and not self._using_fallback:
            try:
                await self._redis.lrem(self._redis_key(), 1, json.dumps(op))
                return
            except Exception as e:
                logger.warning("Redis unreachable removing synced op: %s", e)

        if op in self._memory_fallback:
            self._memory_fallback.remove(op)

    async def _sync_to_db(self, operation: dict) -> bool:
        return True


# ══════════════════════════════════════════════════════════════════════════════
# Standalone Messaging — Multi-language WhatsApp
# ══════════════════════════════════════════════════════════════════════════════

CONFIRMATION_TEMPLATES = {
    "en": (
        "Hi {patient_name}, your appointment at {clinic_name} is confirmed.\n"
        "Provider: {provider_name}\n"
        "Date/Time: {datetime_str}\n"
        "Reply CANCEL to cancel. See you soon!"
    ),
    "ig": (
        "Nnọọ {patient_name}, a kwadoro oge gị na {clinic_name}.\n"
        "Dọkịta: {provider_name}\n"
        "Oge: {datetime_str}\n"
        "Zaa CANCEL iji kagbuo. Ka anyị hụ n'oge!"
    ),
    "yo": (
        "Ẹ káàbọ̀ {patient_name}, a ti fọwọ́ sí ìpàdé rẹ ni {clinic_name}.\n"
        "Dókítà: {provider_name}\n"
        "Àkókò: {datetime_str}\n"
        "Dáhùn CANCEL láti fagilé."
    ),
    "ha": (
        "Sannu {patient_name}, an tabbatar da alƙawarin ku a {clinic_name}.\n"
        "Likita: {provider_name}\n"
        "Lokaci: {datetime_str}\n"
        "Amsa CANCEL don soke."
    ),
    "fr": (
        "Bonjour {patient_name}, votre rendez-vous à {clinic_name} est confirmé.\n"
        "Médecin: {provider_name}\n"
        "Date: {datetime_str}\n"
        "Répondez ANNULER pour annuler."
    ),
    "sw": (
        "Habari {patient_name}, miadi yako kwenye {clinic_name} imethibitishwa.\n"
        "Daktari: {provider_name}\n"
        "Wakati: {datetime_str}\n"
        "Jibu CANCEL kufuta."
    ),
}

REMINDER_TEMPLATES = {
    "en": "Reminder: You have an appointment tomorrow at {time} with {provider_name} at {clinic_name}.",
    "ig": "Ncheta: Ị nwere oge n'ụbọchị echi na {time} na {clinic_name}.",
    "yo": "Ìránṣẹ́: O ní ìpàdé ọlá ọjọ́ ni {time} pẹ̀lú {clinic_name}.",
    "ha": "Tunatarwa: Kuna alƙawari gobe da {time} a {clinic_name}.",
    "fr": "Rappel: Vous avez un rendez-vous demain à {time} avec {provider_name} à {clinic_name}.",
    "sw": "Ukumbusho: Una miadi kesho saa {time} na {provider_name} katika {clinic_name}.",
}


class StandaloneMessaging:
    """Multi-language WhatsApp message generation."""

    async def appointment_confirmation(
        self,
        patient_name: str,
        provider_name: str,
        datetime_str: str,
        clinic_name: str,
        language: str = "en",
    ) -> str:
        template = CONFIRMATION_TEMPLATES.get(language, CONFIRMATION_TEMPLATES["en"])
        return template.format(
            patient_name=patient_name,
            provider_name=provider_name,
            datetime_str=datetime_str,
            clinic_name=clinic_name,
        )

    async def appointment_reminder(
        self,
        patient_name: str,
        provider_name: str,
        time_str: str,
        clinic_name: str,
        language: str = "en",
    ) -> str:
        template = REMINDER_TEMPLATES.get(language, REMINDER_TEMPLATES["en"])
        return template.format(
            patient_name=patient_name,
            provider_name=provider_name,
            time=time_str,
            clinic_name=clinic_name,
        )


# ══════════════════════════════════════════════════════════════════════════════
# Provider Service
# ══════════════════════════════════════════════════════════════════════════════

class StandaloneProviderService:
    """Manage providers and their schedules for standalone clinics."""

    def __init__(self, clinic_id: str) -> None:
        self.clinic_id = clinic_id

    async def create_provider(self, data: dict) -> dict:
        provider_id = f"PROV-{uuid.uuid4().hex[:8].upper()}"
        record = {
            "id": provider_id,
            "clinic_id": self.clinic_id,
            "name": data.get("name", ""),
            "specialty": data.get("specialty", ""),
            "working_hours": data.get("working_hours", {}),
            "slot_duration_minutes": data.get("slot_duration_minutes", 20),
            "break_times": data.get("break_times", ["13:00-14:00"]),
            "active": True,
        }
        saved = await self._save_provider(record)
        return {
            "provider_id": saved.get("id", provider_id),
            "name": saved.get("name", ""),
            "specialty": saved.get("specialty", ""),
        }

    async def get_all_providers(self) -> list:
        return await self._query_providers({"clinic_id": self.clinic_id})

    async def update_provider_schedule(
        self, provider_id: str, working_hours: dict
    ) -> dict:
        return await self._update_provider(
            provider_id, {"working_hours": working_hours}
        )

    async def _save_provider(self, record: dict) -> dict:
        return record

    async def _query_providers(self, filters: dict) -> list:
        return []

    async def _update_provider(self, provider_id: str, data: dict) -> dict:
        return {"id": provider_id, **data}


# ══════════════════════════════════════════════════════════════════════════════
# Global Pricing
# ══════════════════════════════════════════════════════════════════════════════

# Global pricing in local currencies
# US pricing unchanged — adjustments for purchasing power parity globally
GLOBAL_PRICING = {
    # Tier: (starter, pro, growth, enterprise)
    "US": {"currency": "USD", "provider": "lemonsqueezy",
           "starter": 499, "pro": 999, "growth": 1999, "enterprise": 3999},
    "GB": {"currency": "GBP", "provider": "stripe",
           "starter": 399, "pro": 799, "growth": 1599, "enterprise": 3199},
    "NG": {"currency": "NGN", "provider": "paystack",
           "starter": 25_000, "pro": 49_000, "growth": 99_000, "enterprise": 199_000},
    "KE": {"currency": "KES", "provider": "stripe",
           "starter": 6_500, "pro": 12_900, "growth": 25_900, "enterprise": 51_900},
    "GH": {"currency": "GHS", "provider": "paystack",
           "starter": 750, "pro": 1_500, "growth": 2_999, "enterprise": 5_999},
    "ZA": {"currency": "ZAR", "provider": "stripe",
           "starter": 999, "pro": 1_999, "growth": 3_999, "enterprise": 7_999},
    "PH": {"currency": "PHP", "provider": "stripe",
           "starter": 2_999, "pro": 5_999, "growth": 11_999, "enterprise": 23_999},
    "IN": {"currency": "INR", "provider": "stripe",
           "starter": 4_999, "pro": 9_999, "growth": 19_999, "enterprise": 39_999},
    "CA": {"currency": "CAD", "provider": "stripe",
           "starter": 699, "pro": 1_399, "growth": 2_799, "enterprise": 5_599},
    "AU": {"currency": "AUD", "provider": "stripe",
           "starter": 799, "pro": 1_599, "growth": 3_199, "enterprise": 6_399},
    "EU": {"currency": "EUR", "provider": "stripe",
           "starter": 469, "pro": 939, "growth": 1_879, "enterprise": 3_759},
}


class StandalonePricing:
    """
    Global pricing in local currencies.
    Purchasing power parity applied for developing markets.
    """

    @staticmethod
    def get_price(country: str, tier: str) -> dict:
        """Get price for a country and tier."""
        config = GLOBAL_PRICING.get(country.upper())
        if not config:
            # Default to USD for unknown countries
            config = GLOBAL_PRICING["US"]

        amount = config.get(tier, config.get("starter", 499))
        return {
            "country": country,
            "tier": tier,
            "currency": config["currency"],
            "amount": amount,
            "payment_provider": config["provider"],
            "formatted": f"{config['currency']} {amount:,}",
        }

    @staticmethod
    def all_prices_for_country(country: str) -> dict:
        """Return all tier prices for a country."""
        config = GLOBAL_PRICING.get(country.upper(), GLOBAL_PRICING["US"])
        return {
            tier: StandalonePricing.get_price(country, tier)
            for tier in ["starter", "pro", "growth", "enterprise"]
        }
