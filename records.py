"""
Records Agent — HIPAA-compliant medical records handling.

Identity verification is mandatory before any record release.
Every release is audit logged. No exceptions.
"""
import json
import logging
from typing import Optional, Any

from app.agents.base_agent import BaseAgent
from app.security.audit import write_audit_log

logger = logging.getLogger(__name__)


class RecordsAgent(BaseAgent):
    """Records Agent — medical records retrieval and release."""

    agent_type: str = "records"

    def __init__(
        self,
        clinic_id: str,
        llm: Optional[Any] = None,
        memory: Optional[Any] = None,
        ehr: Optional[Any] = None,
    ) -> None:
        super().__init__(clinic_id=clinic_id, llm=llm, memory=memory, ehr=ehr)

    async def verify_patient_identity(
        self,
        call_id: str,
        patient_id: str,
        provided_dob: str,
        provided_last_name: str,
    ) -> dict:
        """Verify patient identity via DOB + last name match."""
        patient = await self.ehr.get_patient(
            clinic_id=self.clinic_id,
            phone="",
        )
        # Fallback: fetch by patient_id
        if not patient:
            try:
                patient = await self.ehr.get_patient_by_id(
                    clinic_id=self.clinic_id,
                    patient_id=patient_id,
                )
            except Exception:
                patient = None

        if not patient:
            return {"verified": False, "reason": "patient_not_found"}

        dob_match = patient.get("date_of_birth", "") == provided_dob
        name_match = patient.get("last_name", "").lower() == provided_last_name.lower()

        if not dob_match:
            return {"verified": False, "reason": "dob_mismatch"}
        if not name_match:
            return {"verified": False, "reason": "name_mismatch"}

        return {"verified": True, "patient_id": patient_id}

    async def classify_record_request(
        self, call_id: str, utterance: str
    ) -> dict:
        """Classify what type of records patient is requesting."""
        response = await self.llm.route(
            task_type="entity_extraction",
            prompt=(
                f"Classify the medical records request.\n\n"
                f"Utterance: \"{utterance}\"\n\n"
                f"Return ONLY valid JSON:\n"
                f'{{"record_type": "<visit_summary|lab_results|imaging|all>", '
                f'"date_range": "<last_3_months|last_6_months|last_year|all>"}}'
            ),
        )
        content = response.get("content", "")
        cleaned = content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return {"record_type": "all", "date_range": "all"}

    async def retrieve_records(
        self,
        call_id: str,
        patient_id: str,
        record_type: str,
    ) -> list:
        """Fetch records from EHR."""
        try:
            return await self.ehr.get_patient_records(
                clinic_id=self.clinic_id,
                patient_id=patient_id,
                record_type=record_type,
            )
        except Exception as e:
            logger.error("Records retrieval failed: %s", str(e))
            return []

    async def request_records_release(
        self,
        call_id: str,
        patient_id: str,
        identity_verified: bool,
        record_type: str,
        recipient: str,
    ) -> dict:
        """Release records — identity verification is mandatory."""
        if not identity_verified:
            return {
                "success": False,
                "blocked_reason": "identity_not_verified",
            }

        try:
            result = await self.ehr.release_records(
                clinic_id=self.clinic_id,
                patient_id=patient_id,
                record_type=record_type,
                recipient=recipient,
            )

            write_audit_log(
                event_type="records_released",
                clinic_id=self.clinic_id,
                call_id=call_id,
                patient_id=patient_id,
                agent_type=self.agent_type,
                metadata={"record_type": record_type, "recipient": recipient},
            )

            await self.memory.add_episode(
                clinic_id=self.clinic_id,
                call_id=call_id,
                episode_type="records_released",
                content=f"Records released: {record_type} to {recipient}.",
                patient_id=patient_id,
                metadata={"record_type": record_type, "recipient": recipient},
            )

            return {
                "success": True,
                "release_id": result.get("release_id"),
                "status": result.get("status", "sent"),
            }

        except Exception as e:
            logger.error("Records release failed: %s", str(e))
            return {"success": False, "error": str(e)}
