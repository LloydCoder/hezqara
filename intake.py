"""
Intake Agent — pre-visit patient data collection.

Runs between scheduling and the appointment itself.
Collects all information the provider needs before the visit:
  - Demographics (DOB, address, email)
  - Insurance (carrier, member ID, group number)
  - Medical history (medications, allergies, conditions)
  - Visit reason and symptoms
  - Validates completeness
  - Writes back to EHR
  - Generates provider summary

Cost discipline:
  - All extraction  → local Ollama (deepseek-coder-v2)
  - Summarization   → local Ollama (qwen2.5:14b)
  - Never needs Claude for any intake task
"""
import json
import logging
from typing import Optional, Any

from app.agents.base_agent import BaseAgent
from app.security.audit import write_audit_log

logger = logging.getLogger(__name__)

# Required fields for a complete intake
REQUIRED_FIELDS = [
    "first_name",
    "last_name",
    "date_of_birth",
    "phone",
]

# All intake fields for completion percentage
ALL_INTAKE_FIELDS = [
    "first_name", "last_name", "date_of_birth", "phone",
    "email", "address", "insurance", "medications",
    "allergies", "visit_reason",
]


class IntakeAgent(BaseAgent):
    """
    Intake Agent — collects patient data before their visit.
    """

    agent_type: str = "intake"

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

    # ── Demographics extraction ───────────────────────────────────────────────

    async def extract_date_of_birth(
        self,
        call_id: str,
        utterance: str,
    ) -> dict:
        """Extract date of birth from natural speech."""
        response = await self.llm.route(
            task_type="entity_extraction",
            prompt=(
                f"Extract the date of birth from this utterance.\n\n"
                f"Utterance: \"{utterance}\"\n\n"
                f"Return ONLY valid JSON in ISO format:\n"
                f'{{"date_of_birth": "YYYY-MM-DD"}}'
            ),
        )
        return self._parse_json(response.get("content", ""))

    async def extract_address(
        self,
        call_id: str,
        utterance: str,
    ) -> dict:
        """Extract street address, city, state, zip from speech."""
        response = await self.llm.route(
            task_type="entity_extraction",
            prompt=(
                f"Extract the mailing address from this utterance.\n\n"
                f"Utterance: \"{utterance}\"\n\n"
                f"Return ONLY valid JSON:\n"
                f'{{"street": "<street>", "city": "<city>", '
                f'"state": "<2-letter state>", "zip": "<zip>"}}'
            ),
        )
        return self._parse_json(response.get("content", ""))

    async def extract_email(
        self,
        call_id: str,
        utterance: str,
    ) -> dict:
        """Extract email address from speech, including spelled-out forms."""
        response = await self.llm.route(
            task_type="entity_extraction",
            prompt=(
                f"Extract the email address from this utterance. "
                f"Convert spoken forms like 'dot' and 'at' to symbols.\n\n"
                f"Utterance: \"{utterance}\"\n\n"
                f"Return ONLY valid JSON:\n"
                f'{{"email": "<email>"}}'
            ),
        )
        return self._parse_json(response.get("content", ""))

    # ── Insurance extraction ──────────────────────────────────────────────────

    async def extract_insurance_info(
        self,
        call_id: str,
        utterance: str,
    ) -> dict:
        """Extract insurance carrier and plan type from speech."""
        response = await self.llm.route(
            task_type="entity_extraction",
            prompt=(
                f"Extract insurance information from this utterance.\n\n"
                f"Utterance: \"{utterance}\"\n\n"
                f"Return ONLY valid JSON:\n"
                f'{{"carrier": "<name or null>", "plan_type": "<HMO|PPO|EPO|null>", '
                f'"uninsured": false}}'
            ),
        )
        return self._parse_json(response.get("content", ""))

    async def extract_member_id(
        self,
        call_id: str,
        utterance: str,
    ) -> dict:
        """Extract insurance member ID and group number from speech."""
        response = await self.llm.route(
            task_type="entity_extraction",
            prompt=(
                f"Extract the insurance member ID and group number from this utterance. "
                f"Ignore spaces between letters and numbers.\n\n"
                f"Utterance: \"{utterance}\"\n\n"
                f"Return ONLY valid JSON:\n"
                f'{{"member_id": "<id>", "group_number": "<group or null>"}}'
            ),
        )
        return self._parse_json(response.get("content", ""))

    # ── Medical history extraction ────────────────────────────────────────────

    async def extract_medications(
        self,
        call_id: str,
        utterance: str,
    ) -> dict:
        """Extract current medications with dose and frequency."""
        response = await self.llm.route(
            task_type="entity_extraction",
            prompt=(
                f"Extract all medications from this utterance.\n\n"
                f"Utterance: \"{utterance}\"\n\n"
                f"Return ONLY valid JSON:\n"
                f'{{"medications": [{{"name": "<drug>", "dose": "<dose>", '
                f'"frequency": "<frequency>"}}]}}'
            ),
        )
        return self._parse_json(response.get("content", ""))

    async def extract_allergies(
        self,
        call_id: str,
        utterance: str,
    ) -> dict:
        """Extract allergies with reaction type. Sets NKDA flag if none."""
        response = await self.llm.route(
            task_type="entity_extraction",
            prompt=(
                f"Extract drug/substance allergies from this utterance.\n\n"
                f"Utterance: \"{utterance}\"\n\n"
                f"Return ONLY valid JSON:\n"
                f'{{"allergies": [{{"substance": "<name>", "reaction": "<reaction>"}}], '
                f'"nkda": false}}\n\n'
                f"Set nkda=true if patient explicitly states no allergies."
            ),
        )
        return self._parse_json(response.get("content", ""))

    async def extract_visit_reason(
        self,
        call_id: str,
        utterance: str,
    ) -> dict:
        """Extract visit reason, symptoms, duration, and severity."""
        response = await self.llm.route(
            task_type="entity_extraction",
            prompt=(
                f"Extract the visit reason and symptoms from this utterance.\n\n"
                f"Utterance: \"{utterance}\"\n\n"
                f"Return ONLY valid JSON:\n"
                f'{{"reason": "<chief complaint>", '
                f'"symptoms": ["<symptom1>", "<symptom2>"], '
                f'"duration": "<duration or null>", '
                f'"severity": <1-10 or null>}}'
            ),
        )
        return self._parse_json(response.get("content", ""))

    # ── Validation ────────────────────────────────────────────────────────────

    def validate_intake(self, intake_data: dict) -> dict:
        """
        Validate intake data for completeness.
        Returns valid flag, missing fields, and completion percentage.
        """
        missing = [
            field for field in REQUIRED_FIELDS
            if not intake_data.get(field)
        ]

        filled = sum(
            1 for field in ALL_INTAKE_FIELDS
            if intake_data.get(field) is not None
        )
        completion_pct = round((filled / len(ALL_INTAKE_FIELDS)) * 100)

        return {
            "valid": len(missing) == 0,
            "missing_fields": missing,
            "completion_pct": completion_pct,
        }

    # ── EHR write-back ────────────────────────────────────────────────────────

    async def submit_intake_to_ehr(
        self,
        call_id: str,
        patient_id: Optional[str],
        intake_data: dict,
    ) -> dict:
        """
        Write intake data to EHR.
        New patient → create_patient.
        Existing patient → update_patient.
        """
        try:
            if patient_id:
                result = await self.ehr.update_patient(
                    clinic_id=self.clinic_id,
                    patient_id=patient_id,
                    data=intake_data,
                )
                ehr_patient_id = patient_id
            else:
                result = await self.ehr.create_patient(
                    clinic_id=self.clinic_id,
                    data=intake_data,
                )
                ehr_patient_id = result.get("patient_id")

            # HIPAA audit log
            write_audit_log(
                event_type="intake_submitted",
                clinic_id=self.clinic_id,
                call_id=call_id,
                patient_id=ehr_patient_id,
                agent_type=self.agent_type,
                metadata={"fields_collected": list(intake_data.keys())},
            )

            # Store in Graphiti
            await self.memory.add_episode(
                clinic_id=self.clinic_id,
                call_id=call_id,
                episode_type="intake_completed",
                content=f"Intake collected. Fields: {', '.join(intake_data.keys())}.",
                patient_id=ehr_patient_id,
                metadata={"fields": list(intake_data.keys())},
            )

            return {
                "success": True,
                "patient_id": ehr_patient_id,
            }

        except Exception as e:
            logger.error(
                "Intake EHR submission failed for call %s: %s",
                call_id, str(e)
            )
            return {"success": False, "error": str(e)}

    # ── Provider summary ──────────────────────────────────────────────────────

    async def generate_provider_summary(
        self,
        call_id: str,
        intake_data: dict,
    ) -> str:
        """
        Generate a concise intake summary for the provider.
        Local LLM — routine summarization, never needs Claude.
        """
        intake_text = json.dumps(intake_data, indent=2)

        response = await self.llm.route(
            task_type="patient_intake_summarize",
            prompt=(
                f"Generate a concise clinical intake summary for a provider.\n\n"
                f"Intake data:\n{intake_text}\n\n"
                f"Format: 2-3 sentences. Include patient name, DOB, "
                f"chief complaint, key medications, and allergies. "
                f"Use clinical abbreviations (NKDA, HTN, DM2 etc)."
            ),
        )

        return response.get("content", "Intake data collected. See EHR for details.")

    # ── Private helpers ───────────────────────────────────────────────────────

    def _parse_json(self, content: str) -> dict:
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
            logger.warning("Failed to parse JSON: %s", content[:100])
            return {}
