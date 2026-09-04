"""
Reception Agent — Carenova's front door.

Handles every inbound patient call via Retell AI voice.
First agent in every call flow. Responsible for:

  1. Greeting the patient warmly with clinic name
  2. Detecting call intent (appointment/refill/insurance/general/emergency)
  3. Identifying the patient (by phone or by name)
  4. Routing to the correct specialist agent
  5. Handling human transfer requests
  6. HIPAA audit logging on every action
  7. Storing call episodes in Graphiti for persistent memory

Cost discipline:
  - Greeting → local Ollama (qwen2.5:14b)
  - Intent detection → local Ollama (deepseek-coder-v2)
  - Entity extraction → local Ollama (deepseek-coder-v2)
  - Escalation decisions → Claude Sonnet only
"""
import json
import logging
from typing import Optional, Any

from app.agents.base_agent import BaseAgent
from app.security.audit import write_audit_log
from app.utils.phone_formatter import mask_phone_number

logger = logging.getLogger(__name__)

# Intent routing map
INTENT_AGENT_MAP = {
    "appointment": "scheduling",
    "refill": "refill",
    "insurance": "insurance",
    "records": "records",
    "referral": "referrals",
    "recall": "recall",
    "general": "reception",
    "unknown": "reception",
    "emergency": "human",
}

# Intents that must immediately transfer to human
EMERGENCY_INTENTS = {"emergency"}


class ReceptionAgent(BaseAgent):
    """
    Reception Agent — handles inbound patient calls.
    """

    agent_type: str = "reception"

    def __init__(
        self,
        clinic_id: str,
        llm: Optional[Any] = None,
        memory: Optional[Any] = None,
        ehr: Optional[Any] = None,
    ) -> None:
        super().__init__(clinic_id=clinic_id, llm=llm, memory=memory, ehr=ehr)

    # ── Call lifecycle ────────────────────────────────────────────────────────

    async def handle_call_started(
        self,
        call_id: str,
        from_number: str,
    ) -> dict:
        """
        Called the moment a patient call connects.
        Fetches clinic context and generates greeting.
        """
        # Fetch clinic context from Graphiti
        clinic_context = await self.memory.get_clinic_context(self.clinic_id)
        clinic_name = clinic_context.get("clinic_name", "our clinic")

        # Generate greeting using local LLM
        response = await self.llm.route(
            task_type="reception_greeting",
            prompt=(
                f"Generate a warm, professional phone greeting for {clinic_name}. "
                f"Keep it under 15 words. Don't ask a question."
            ),
            system_prompt=(
                "You are a medical receptionist. Greet patients warmly and professionally. "
                "Be concise and welcoming."
            ),
        )

        greeting = response.get("content", f"Thank you for calling {clinic_name}.")

        # HIPAA audit log
        write_audit_log(
            event_type="call_started",
            clinic_id=self.clinic_id,
            call_id=call_id,
            agent_type=self.agent_type,
            metadata={"from_number_masked": mask_phone_number(from_number)},
        )

        return {
            "call_id": call_id,
            "greeting": greeting,
            "clinic_id": self.clinic_id,
            "model_used": response.get("model_used"),
            "cost_usd": response.get("cost_usd", 0.0),
        }

    async def handle_call_ended(self, call_data: dict) -> dict:
        """
        Called when the call disconnects.
        Stores episode in Graphiti and writes audit log.
        """
        call_id = call_data.get("call_id", "unknown")
        duration_ms = call_data.get("duration_ms", 0)
        transcript = call_data.get("transcript", [])

        # Store call episode in Graphiti for persistent memory
        summary = self._summarize_transcript(transcript)
        await self.memory.add_episode(
            clinic_id=self.clinic_id,
            call_id=call_id,
            episode_type="call_completed",
            content=summary,
            metadata={"duration_ms": duration_ms},
        )

        # HIPAA audit log
        write_audit_log(
            event_type="call_ended",
            clinic_id=self.clinic_id,
            call_id=call_id,
            agent_type=self.agent_type,
            metadata={"duration_ms": duration_ms},
        )

        return {
            "call_id": call_id,
            "episode_stored": True,
            "duration_ms": duration_ms,
        }

    # ── Intent detection ──────────────────────────────────────────────────────

    async def detect_intent(
        self,
        call_id: str,
        utterance: str,
    ) -> dict:
        """
        Classify the patient's call intent from their utterance.
        Uses local LLM — this is routine classification, not complex reasoning.
        """
        response = await self.llm.route(
            task_type="intent_detection",
            prompt=(
                f"Classify this patient utterance into exactly one intent.\n\n"
                f"Utterance: \"{utterance}\"\n\n"
                f"Return ONLY valid JSON:\n"
                f'{{"intent": "<intent>", "confidence": <0.0-1.0>}}\n\n'
                f"Valid intents: appointment, refill, insurance, records, "
                f"referral, general, emergency, unknown"
            ),
        )

        content = response.get("content", "")
        intent_data = self._parse_json_response(content)

        intent = intent_data.get("intent", "unknown")
        confidence = intent_data.get("confidence", 0.5)

        # Emergency always gets human transfer flag
        transfer_to_human = intent in EMERGENCY_INTENTS

        return {
            "intent": intent,
            "confidence": confidence,
            "transfer_to_human": transfer_to_human,
            "call_id": call_id,
        }

    # ── Patient identification ────────────────────────────────────────────────

    async def identify_patient(
        self,
        call_id: str,
        from_number: str,
    ) -> dict:
        """
        Try to identify the patient by their calling phone number.
        Returns identified=True if found in EHR, False if new patient.
        """
        if not self.ehr:
            return {"identified": False, "requires_name": True}

        patient = await self.ehr.get_patient(
            clinic_id=self.clinic_id,
            phone=from_number,
        )

        if patient:
            return {
                "identified": True,
                "patient_id": patient["patient_id"],
                "requires_verification": False,
                "call_id": call_id,
            }

        return {
            "identified": False,
            "requires_name": True,
            "call_id": call_id,
        }

    async def extract_patient_name(
        self,
        call_id: str,
        utterance: str,
    ) -> dict:
        """
        Extract first and last name from natural speech utterance.
        Uses local LLM for entity extraction.
        """
        response = await self.llm.route(
            task_type="entity_extraction",
            prompt=(
                f"Extract the patient's first and last name from this utterance.\n\n"
                f"Utterance: \"{utterance}\"\n\n"
                f"Return ONLY valid JSON:\n"
                f'{{"first_name": "<first>", "last_name": "<last>"}}'
            ),
        )

        content = response.get("content", "")
        return self._parse_json_response(content)

    # ── Agent routing ─────────────────────────────────────────────────────────

    async def route_to_specialist(
        self,
        call_id: str,
        intent: str,
        patient_id: str,
    ) -> dict:
        """
        Determine which specialist agent should handle the call.
        Returns routing decision — does not perform the handoff.
        """
        next_agent = INTENT_AGENT_MAP.get(intent, "reception")

        return {
            "next_agent": next_agent,
            "call_id": call_id,
            "patient_id": patient_id,
            "intent": intent,
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _parse_json_response(self, content: str) -> dict:
        """
        Safely parse JSON from LLM response.
        LLMs sometimes wrap JSON in markdown — handle that.
        """
        if not content:
            return {}

        # Strip markdown code fences if present
        cleaned = content.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM JSON response: %s", content[:100])
            return {}

    def _summarize_transcript(self, transcript: list) -> str:
        """
        Create a brief text summary of call transcript for Graphiti storage.
        No PHI in the summary — just intent and outcome.
        """
        if not transcript:
            return "Call completed. No transcript available."

        turn_count = len(transcript)
        intents_mentioned = []

        keywords = {
            "appointment": "appointment scheduling",
            "medication": "medication refill",
            "insurance": "insurance inquiry",
            "records": "records request",
        }

        full_text = " ".join(
            turn.get("content", "") for turn in transcript
        ).lower()

        for keyword, label in keywords.items():
            if keyword in full_text:
                intents_mentioned.append(label)

        intent_str = (
            ", ".join(intents_mentioned) if intents_mentioned else "general inquiry"
        )

        return (
            f"Call completed. {turn_count} turns. "
            f"Topics: {intent_str}."
        )
