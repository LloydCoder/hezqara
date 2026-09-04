"""
Scheduling Agent — appointment booking for Carenova.

The most-used agent. Handles:
  - Fetching available slots from athenahealth EHR
  - Extracting patient scheduling preference from speech
  - Matching preference to best available slot
  - Booking appointment with write-back to EHR
  - Generating verbal confirmation for patient
  - Detecting reschedule and cancellation intents
  - Cancelling appointments with EHR write-back
  - HIPAA audit logging on every action
  - Graphiti episode storage for recall agent

Cost discipline:
  - Preference extraction → local Ollama (deepseek-coder-v2)
  - Slot matching        → local Ollama (deepseek-coder-v2)
  - Confirmation text    → local Ollama (qwen2.5:14b)
  - Action detection     → local Ollama (deepseek-coder-v2)
  - Never needs Claude for any scheduling task
"""
import json
import logging
from typing import Optional, Any

from app.agents.base_agent import BaseAgent
from app.security.audit import write_audit_log

logger = logging.getLogger(__name__)

# Scheduling actions
SCHEDULING_ACTIONS = {"book", "reschedule", "cancel", "check"}


class SchedulingAgent(BaseAgent):
    """
    Scheduling Agent — handles all appointment booking flows.
    """

    agent_type: str = "scheduling"

    def __init__(
        self,
        clinic_id: str,
        llm: Optional[Any] = None,
        memory: Optional[Any] = None,
        ehr: Optional[Any] = None,
    ) -> None:
        super().__init__(
            clinic_id=clinic_id,
            llm=llm,
            memory=memory,
            ehr=ehr,
        )

    # ── Slot fetching ─────────────────────────────────────────────────────────

    async def get_available_slots(
        self,
        call_id: str,
        provider_id: str,
        requested_date: str,
        reason: Optional[str] = None,
    ) -> list:
        """
        Fetch available appointment slots from EHR.
        Multi-tenant: clinic_id always travels with the request.
        """
        try:
            slots = await self.ehr.get_available_slots(
                clinic_id=self.clinic_id,
                provider_id=provider_id,
                date=requested_date,
                reason=reason,
            )
            return slots or []

        except Exception as e:
            logger.warning(
                "Failed to fetch slots for clinic %s: %s",
                self.clinic_id, str(e)
            )
            return []

    async def filter_slots_by_provider(
        self,
        slots: list,
        provider_id: str,
    ) -> list:
        """Filter slot list to a specific provider."""
        return [s for s in slots if s.get("provider_id") == provider_id]

    # ── Preference extraction ─────────────────────────────────────────────────

    async def extract_scheduling_preference(
        self,
        call_id: str,
        utterance: str,
    ) -> dict:
        """
        Extract scheduling preference from patient's natural speech.
        Uses local LLM — routine entity extraction.
        """
        response = await self.llm.route(
            task_type="appointment_slot_select",
            prompt=(
                f"Extract scheduling preferences from this patient utterance.\n\n"
                f"Utterance: \"{utterance}\"\n\n"
                f"Return ONLY valid JSON:\n"
                f'{{"day_preference": "<day or any>", '
                f'"time_preference": "<morning|afternoon|evening|any>", '
                f'"provider_preference": "<name or null>", '
                f'"reason": "<visit reason or null>"}}'
            ),
        )

        return self._parse_json_response(response.get("content", ""))

    async def match_slot_to_preference(
        self,
        call_id: str,
        slots: list,
        patient_preference: str,
    ) -> Optional[dict]:
        """
        Select the best slot from available options based on preference.
        Uses local LLM for matching logic.
        """
        if not slots:
            return None

        slots_text = json.dumps(slots, indent=2)

        response = await self.llm.route(
            task_type="appointment_slot_select",
            prompt=(
                f"Select the best appointment slot for a patient who wants: "
                f"'{patient_preference}'\n\n"
                f"Available slots:\n{slots_text}\n\n"
                f"Return ONLY valid JSON:\n"
                f'{{"slot_id": "<id>", "reason": "<brief reason>"}}'
            ),
        )

        result = self._parse_json_response(response.get("content", ""))

        if "slot_id" in result:
            matched = next(
                (s for s in slots if s["slot_id"] == result["slot_id"]),
                slots[0],
            )
            return matched

        return slots[0] if slots else None

    # ── Booking ───────────────────────────────────────────────────────────────

    async def book_appointment(
        self,
        call_id: str,
        patient_id: str,
        slot_id: str,
        reason: str,
    ) -> dict:
        """
        Book appointment with write-back to EHR.
        Write-back is the core value — not just local storage.
        """
        try:
            booking = await self.ehr.book_appointment(
                clinic_id=self.clinic_id,
                patient_id=patient_id,
                slot_id=slot_id,
                reason=reason,
            )

            appointment_id = booking.get("appointment_id")

            # HIPAA audit log
            write_audit_log(
                event_type="appointment_booked",
                clinic_id=self.clinic_id,
                call_id=call_id,
                patient_id=patient_id,
                agent_type=self.agent_type,
                metadata={"appointment_id": appointment_id, "slot_id": slot_id},
            )

            # Store episode in Graphiti — feeds recall agent later
            await self.memory.add_episode(
                clinic_id=self.clinic_id,
                call_id=call_id,
                episode_type="appointment_booked",
                content=f"Appointment booked. Reason: {reason}.",
                patient_id=patient_id,
                metadata={
                    "appointment_id": appointment_id,
                    "slot_id": slot_id,
                    "reason": reason,
                },
            )

            return {
                "success": True,
                "appointment_id": appointment_id,
                "datetime": booking.get("datetime"),
                "provider": booking.get("provider"),
                "slot_id": slot_id,
            }

        except Exception as e:
            logger.error(
                "Booking failed for patient %s slot %s: %s",
                patient_id, slot_id, str(e)
            )
            return {
                "success": False,
                "error": str(e),
                "slot_id": slot_id,
            }

    async def generate_confirmation_message(
        self,
        appointment: dict,
    ) -> str:
        """
        Generate a warm verbal confirmation for the patient.
        Uses local LLM — routine text generation.
        """
        dt = appointment.get("datetime", "")
        provider = appointment.get("provider", "your provider")

        response = await self.llm.route(
            task_type="appointment_reminder_text",
            prompt=(
                f"Generate a brief, warm appointment confirmation message.\n"
                f"Provider: {provider}\n"
                f"DateTime: {dt}\n\n"
                f"Keep under 30 words. Be friendly. "
                f"Mention the provider name and date/time."
            ),
        )

        return response.get("content", (
            f"Your appointment with {provider} is confirmed for {dt}."
        ))

    # ── Reschedule and cancellation ───────────────────────────────────────────

    async def detect_scheduling_action(
        self,
        call_id: str,
        utterance: str,
    ) -> dict:
        """
        Detect whether patient wants to book, reschedule, or cancel.
        """
        response = await self.llm.route(
            task_type="appointment_slot_select",
            prompt=(
                f"Classify this scheduling utterance.\n\n"
                f"Utterance: \"{utterance}\"\n\n"
                f"Return ONLY valid JSON:\n"
                f'{{"action": "<book|reschedule|cancel|check>", '
                f'"confidence": <0.0-1.0>}}'
            ),
        )

        return self._parse_json_response(response.get("content", ""))

    async def cancel_appointment(
        self,
        call_id: str,
        patient_id: str,
        appointment_id: str,
    ) -> dict:
        """
        Cancel appointment with EHR write-back to free the slot.
        """
        try:
            result = await self.ehr.cancel_appointment(
                clinic_id=self.clinic_id,
                patient_id=patient_id,
                appointment_id=appointment_id,
            )

            write_audit_log(
                event_type="appointment_cancelled",
                clinic_id=self.clinic_id,
                call_id=call_id,
                patient_id=patient_id,
                agent_type=self.agent_type,
                metadata={"appointment_id": appointment_id},
            )

            return {"success": True, "appointment_id": appointment_id}

        except Exception as e:
            logger.error(
                "Cancellation failed for appointment %s: %s",
                appointment_id, str(e)
            )
            return {"success": False, "error": str(e)}

    # ── Private helpers ───────────────────────────────────────────────────────

    def _parse_json_response(self, content: str) -> dict:
        """Safely parse JSON from LLM response."""
        if not content:
            return {}

        cleaned = content.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning(
                "Failed to parse LLM JSON: %s", content[:100]
            )
            return {}
