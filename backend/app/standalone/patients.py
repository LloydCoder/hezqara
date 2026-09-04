"""
Standalone Patient Service.
Supabase is the EHR. No external system. Full patient lifecycle.
"""
import logging
import uuid
from typing import Optional

logger = logging.getLogger(__name__)


class StandalonePatientService:
    """
    Manages patient records directly in Supabase.
    Works globally — no EHR vendor dependency.
    """

    def __init__(self, clinic_id: str) -> None:
        self.clinic_id = clinic_id

    async def create_patient(self, data: dict) -> dict:
        """Create patient in Supabase. Returns patient dict."""
        patient_id = f"PAT-{uuid.uuid4().hex[:8].upper()}"
        record = {
            "id": patient_id,
            "clinic_id": self.clinic_id,
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
            "phone": data.get("phone", ""),
            "email": data.get("email", ""),
            "date_of_birth": data.get("date_of_birth"),
            "gender": data.get("gender"),
            "address_street": data.get("street"),
            "address_city": data.get("city"),
            "address_country": data.get("country", ""),
            "language": data.get("language", "en"),
            "notes": data.get("notes", ""),
        }
        saved = await self._save_to_db(record)
        return {
            "patient_id": saved.get("id", patient_id),
            "first_name": saved.get("first_name", ""),
            "last_name": saved.get("last_name", ""),
            "phone": saved.get("phone", ""),
            "clinic_id": self.clinic_id,
        }

    async def find_patient_by_phone(self, phone: str) -> Optional[dict]:
        """Search by phone number. Returns None if not found."""
        digits = "".join(c for c in phone if c.isdigit())[-10:]
        rows = await self._query_db({"phone_digits": digits})
        if not rows:
            return None
        p = rows[0]
        return {
            "patient_id": p.get("id", ""),
            "first_name": p.get("first_name", ""),
            "last_name": p.get("last_name", ""),
            "phone": p.get("phone", ""),
            "date_of_birth": p.get("date_of_birth"),
            "gender": p.get("gender"),
        }

    async def search_patient(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        date_of_birth: Optional[str] = None,
    ) -> Optional[dict]:
        """Search by name + DOB."""
        query: dict = {}
        if first_name:
            query["first_name"] = first_name
        if last_name:
            query["last_name"] = last_name
        if date_of_birth:
            query["date_of_birth"] = date_of_birth
        rows = await self._query_db(query)
        if not rows:
            return None
        p = rows[0]
        return {
            "patient_id": p.get("id", ""),
            "first_name": p.get("first_name", ""),
            "last_name": p.get("last_name", ""),
            "phone": p.get("phone", ""),
        }

    async def update_patient(self, patient_id: str, data: dict) -> Optional[dict]:
        """Update patient fields in Supabase."""
        return await self._update_db(patient_id=patient_id, data=data)

    async def get_visit_history(self, patient_id: str) -> list:
        """Return all visit records for a patient."""
        return await self._query_db(
            {"patient_id": patient_id, "table": "visits"}
        )

    async def get_all_patients(self, limit: int = 100, offset: int = 0) -> list:
        """Return paginated patient list for clinic dashboard."""
        return await self._query_db(
            {"clinic_id": self.clinic_id, "limit": limit, "offset": offset}
        )

    # ── DB layer — replaced in production with real Supabase calls ──

    async def _save_to_db(self, record: dict) -> dict:
        """Production: INSERT into patients table."""
        return record

    async def _query_db(self, filters: dict) -> list:
        """Production: SELECT from patients table."""
        return []

    async def _update_db(self, patient_id: str, data: dict) -> dict:
        """Production: UPDATE patients table."""
        return {"id": patient_id, **data}
