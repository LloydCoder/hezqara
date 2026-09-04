"""
Queue Manager — Real-time walk-in queue for any clinic globally.

Designed for the African and Asian walk-in reality:
  - 50+ patients arriving in morning rush
  - 2-3 doctors seeing patients simultaneously
  - Nurses managing check-in and records manually
  - No computers — nurses use phones
  - Power outages — must recover state

Features:
  - Real-time queue with position and wait time
  - Emergency priority queue (jump to front)
  - Doctor calls next patient → WhatsApp notification sent
  - Visit completion with follow-up scheduling
  - Multi-provider support (different queues per doctor)
  - Dashboard stats for clinic management
"""
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.walkin.messages import WalkInMessages
from app.services.whatsapp_templates import WhatsAppTemplateService

logger = logging.getLogger(__name__)

# Average consultation duration — used for wait time estimates
DEFAULT_CONSULT_MINUTES = 12


class QueueEntry:
    """A single patient in the queue."""

    def __init__(
        self,
        patient_name: str,
        chief_complaint: str,
        queue_number: int,
        patient_phone: Optional[str] = None,
        patient_id: Optional[str] = None,
        language: str = "en",
        priority: str = "normal",
    ) -> None:
        self.visit_id = f"VISIT-{uuid.uuid4().hex[:8].upper()}"
        self.patient_name = patient_name
        self.chief_complaint = chief_complaint
        self.queue_number = queue_number
        self.patient_phone = patient_phone
        self.patient_id = patient_id
        self.language = language
        self.priority = priority  # "normal" | "emergency" | "urgent"
        self.status = "waiting"   # waiting | called | completed | no_show
        self.checked_in_at = datetime.utcnow()
        self.called_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.provider_id: Optional[str] = None
        self.room: Optional[str] = None
        self.notes: Optional[str] = None
        self.follow_up_days: Optional[int] = None


class QueueManager:
    """
    Manages the walk-in queue for a clinic.

    In production: backed by Supabase with real-time subscriptions.
    The nurse's screen updates live as patients are added.
    The doctor's screen updates live as the queue changes.
    """

    def __init__(self, clinic_id: str) -> None:
        self.clinic_id = clinic_id
        self._queue: list[QueueEntry] = []  # In-memory (Supabase in production)
        self._counter: int = 0
        self._avg_consult_minutes: int = DEFAULT_CONSULT_MINUTES

    # ── Queue operations ──────────────────────────────────────────────────────

    async def enqueue(self, data: dict) -> dict:
        """
        Add a walk-in patient to the queue.
        Emergency patients jump to the front.
        Returns queue entry with position and estimated wait.
        """
        self._counter += 1
        priority = data.get("priority", "normal")

        entry = QueueEntry(
            patient_name=data.get("patient_name", "Unknown"),
            chief_complaint=data.get("chief_complaint", ""),
            queue_number=self._counter,
            patient_phone=data.get("patient_phone"),
            patient_id=data.get("patient_id"),
            language=data.get("language", "en"),
            priority=priority,
        )
        entry.visit_id = data.get("visit_id", entry.visit_id)

        # Emergencies go to front of queue
        if priority == "emergency":
            # Insert after any other emergencies but before normal patients
            insert_at = 0
            for i, e in enumerate(self._queue):
                if e.status == "waiting" and e.priority == "emergency":
                    insert_at = i + 1
            self._queue.insert(insert_at, entry)
        else:
            self._queue.append(entry)

        position = self._get_position(entry.visit_id)
        wait = await self.get_estimated_wait_minutes(position=position)

        logger.info(
            "Walk-in enqueued: clinic=%s name=%s complaint=%s queue=%d",
            self.clinic_id, entry.patient_name[:20],
            entry.chief_complaint[:20], entry.queue_number
        )

        return {
            "visit_id": entry.visit_id,
            "queue_number": entry.queue_number,
            "position": position,
            "status": "waiting",
            "estimated_wait_minutes": wait,
            "priority": priority,
            "checked_in_at": entry.checked_in_at.isoformat(),
        }

    async def get_queue(self, provider_id: Optional[str] = None) -> dict:
        """
        Get current queue state — for nurse and doctor screens.
        Shows: waiting, called, completed today.
        """
        waiting = [
            {
                "visit_id": e.visit_id,
                "queue_number": e.queue_number,
                "patient_name": e.patient_name,
                "patient_phone": (e.patient_phone[:4] + "****") if e.patient_phone else None,
                "chief_complaint": e.chief_complaint,
                "priority": e.priority,
                "status": e.status,
                "wait_minutes": int(
                    (datetime.utcnow() - e.checked_in_at).total_seconds() / 60
                ),
                "language": e.language,
            }
            for e in self._queue
            if e.status == "waiting"
        ]

        called = [
            {
                "visit_id": e.visit_id,
                "queue_number": e.queue_number,
                "patient_name": e.patient_name,
                "room": e.room,
                "provider_id": e.provider_id,
            }
            for e in self._queue
            if e.status == "called"
        ]

        completed = [
            e for e in self._queue if e.status == "completed"
        ]

        total_waiting = len(waiting)
        est_wait = await self.get_estimated_wait_minutes()

        return {
            "clinic_id": self.clinic_id,
            "total_waiting": total_waiting,
            "total_called": len(called),
            "total_completed_today": len(completed),
            "estimated_wait_minutes": est_wait,
            "waiting": waiting,
            "called": called,
            "updated_at": datetime.utcnow().isoformat(),
        }

    async def call_next(
        self,
        provider_id: str,
        room: str = "Room 1",
    ) -> dict:
        """
        Doctor calls the next patient.
        Sends WhatsApp notification to patient.
        Updates queue status in real time.
        """
        # Find next waiting patient (emergencies first)
        next_patient = None
        for entry in self._queue:
            if entry.status == "waiting":
                next_patient = entry
                break

        if not next_patient:
            return {"error": "Queue is empty", "queue_empty": True}

        next_patient.status = "called"
        next_patient.called_at = datetime.utcnow()
        next_patient.provider_id = provider_id
        next_patient.room = room

        # Notify patient via WhatsApp
        if next_patient.patient_phone:
            message = WalkInMessages.called_notification(
                language=next_patient.language,
                room=room,
                provider_name="the doctor",
            )
            await self._send_whatsapp_notification(
                phone=next_patient.patient_phone,
                message=message,
            )

        logger.info(
            "Patient called: clinic=%s name=%s room=%s provider=%s",
            self.clinic_id, next_patient.patient_name, room, provider_id
        )

        return {
            "visit_id": next_patient.visit_id,
            "queue_number": next_patient.queue_number,
            "patient_name": next_patient.patient_name,
            "chief_complaint": next_patient.chief_complaint,
            "room": room,
            "status": "called",
            "notified": next_patient.patient_phone is not None,
            "remaining_in_queue": sum(
                1 for e in self._queue if e.status == "waiting"
            ),
        }

    async def complete_visit(
        self,
        visit_id: str,
        notes: str = "",
        follow_up_days: Optional[int] = None,
        diagnosis: Optional[str] = None,
    ) -> dict:
        """
        Doctor marks visit as complete.
        Schedules follow-up reminder if follow_up_days provided.
        """
        entry = self._find_entry(visit_id)
        if not entry:
            return {"error": f"Visit {visit_id} not found"}

        entry.status = "completed"
        entry.completed_at = datetime.utcnow()
        entry.notes = notes
        entry.follow_up_days = follow_up_days

        # Update average consultation time
        if entry.called_at:
            consult_mins = int(
                (entry.completed_at - entry.called_at).total_seconds() / 60
            )
            if 2 <= consult_mins <= 60:
                self._avg_consult_minutes = int(
                    (self._avg_consult_minutes * 0.8) + (consult_mins * 0.2)
                )

        # Schedule follow-up reminder
        follow_up_scheduled = False
        if follow_up_days and entry.patient_phone:
            await self._queue_followup_reminder(
                patient_phone=entry.patient_phone,
                patient_name=entry.patient_name,
                language=entry.language,
                follow_up_days=follow_up_days,
                clinic_id=self.clinic_id,
            )
            follow_up_scheduled = True

        logger.info(
            "Visit completed: clinic=%s visit=%s follow_up=%s",
            self.clinic_id, visit_id, follow_up_days
        )

        return {
            "visit_id": visit_id,
            "status": "completed",
            "notes_saved": bool(notes),
            "follow_up_scheduled": follow_up_scheduled,
            "follow_up_days": follow_up_days,
            "completed_at": entry.completed_at.isoformat(),
        }

    async def mark_no_show(self, visit_id: str) -> dict:
        """Patient was called but did not come in."""
        entry = self._find_entry(visit_id)
        if not entry:
            return {"error": "Visit not found"}
        entry.status = "no_show"
        return {"visit_id": visit_id, "status": "no_show"}

    # ── Stats and analytics ───────────────────────────────────────────────────

    async def get_estimated_wait_minutes(
        self,
        position: Optional[int] = None,
    ) -> int:
        """
        Estimate wait time based on:
        - Number of patients currently waiting
        - Average consultation time (updated dynamically)
        - Number of active providers
        """
        waiting_count = sum(1 for e in self._queue if e.status == "waiting")
        active_providers = max(1, sum(1 for e in self._queue if e.status == "called"))

        if position is not None:
            patients_before = position - 1
        else:
            patients_before = waiting_count

        wait = (patients_before * self._avg_consult_minutes) // active_providers
        return max(5, wait)

    async def get_stats(self) -> dict:
        """Dashboard stats — total today, avg wait, throughput."""
        total = len(self._queue)
        waiting = sum(1 for e in self._queue if e.status == "waiting")
        called = sum(1 for e in self._queue if e.status == "called")
        completed = sum(1 for e in self._queue if e.status == "completed")
        no_show = sum(1 for e in self._queue if e.status == "no_show")

        completed_entries = [e for e in self._queue if e.status == "completed"
                             and e.called_at and e.completed_at]
        avg_consult = self._avg_consult_minutes
        if completed_entries:
            avg_consult = int(sum(
                (e.completed_at - e.called_at).total_seconds() / 60
                for e in completed_entries
            ) / len(completed_entries))

        return {
            "clinic_id": self.clinic_id,
            "date": date.today().isoformat() if False else datetime.utcnow().date().isoformat(),
            "total_today": total,
            "currently_waiting": waiting,
            "currently_with_doctor": called,
            "completed_today": completed,
            "no_shows_today": no_show,
            "avg_wait_minutes": await self.get_estimated_wait_minutes(),
            "avg_consult_minutes": avg_consult,
            "throughput_per_hour": max(0, int(60 / max(avg_consult, 1))),
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_position(self, visit_id: str) -> int:
        """Get current queue position for a visit."""
        waiting = [e for e in self._queue if e.status == "waiting"]
        for i, e in enumerate(waiting, 1):
            if e.visit_id == visit_id:
                return i
        return 0

    def _find_entry(self, visit_id: str) -> Optional[QueueEntry]:
        for e in self._queue:
            if e.visit_id == visit_id:
                return e
        return None

    async def _send_whatsapp_notification(self, phone: str, message: str) -> None:
        """Send WhatsApp notification. Production: Twilio / WhatsApp Business API."""
        logger.info("WhatsApp → %s: %s", phone[:4] + "****", message[:50])

    async def _queue_followup_reminder(
        self,
        patient_phone: str,
        patient_name: str,
        language: str,
        follow_up_days: int,
        clinic_id: str,
    ) -> None:
        """
        Queue a follow-up reminder for future delivery.

        Follow-up reminders are always sent days after the visit — well
        outside WhatsApp's 24-hour free service window — so they must use
        a pre-approved utility template, not free-form text, or Meta will
        block delivery.
        """
        decision = WhatsAppTemplateService().decide_message_type(
            last_patient_message_hours_ago=follow_up_days * 24,
            message_purpose="followup_reminder",
        )

        message_text = WalkInMessages.followup_reminder(
            language=language,
            patient_name=patient_name,
            clinic_name="your clinic",
            days_from_now=follow_up_days,
        )

        logger.info(
            "Follow-up reminder queued: clinic=%s patient=%s days=%d use_template=%s",
            clinic_id, patient_name[:10], follow_up_days, decision["use_template"],
        )

        await self._send_whatsapp_notification(phone=patient_phone, message=message_text)


# Import date for stats
from datetime import date
