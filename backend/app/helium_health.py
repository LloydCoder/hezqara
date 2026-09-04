"""
Helium Health EHR Client — Nigeria's leading EMR.
Used by 100+ hospitals and clinics across Africa.
REST API with facility_id-based multi-tenancy.
"""
import logging
from typing import Optional
import httpx

from app.ehr.base import BaseEHR

logger = logging.getLogger(__name__)
HELIUM_BASE = "https://api.heliumhealth.com/v1"


class HeliumHealthClient(BaseEHR):
    """Helium Health EMR client for Nigerian clinics."""

    def __init__(self, api_key: str, facility_id: str) -> None:
        self.api_key = api_key
        self.facility_id = facility_id

    async def get_patient(self, clinic_id: str, phone: str) -> Optional[dict]:
        """Look up patient by phone number."""
        digits = phone.replace("+234", "0").replace("+", "")[-11:]
        try:
            data = await self._get(
                f"/facilities/{self.facility_id}/patients",
                params={"phone": digits},
            )
            patients = data.get("data", [])
            if not patients:
                return None
            p = patients[0]
            return {
                "patient_id": str(p.get("id", "")),
                "first_name": p.get("first_name", ""),
                "last_name": p.get("last_name", ""),
                "phone": p.get("phone", ""),
            }
        except Exception as e:
            logger.error("Helium get_patient failed: %s", str(e))
            return None

    async def create_patient(self, clinic_id: str, data: dict) -> dict:
        """Register new patient in Helium Health."""
        payload = {
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
            "phone": data.get("phone", ""),
            "date_of_birth": data.get("date_of_birth", ""),
        }
        result = await self._post(
            f"/facilities/{self.facility_id}/patients", payload
        )
        return {"patient_id": str(result.get("data", {}).get("id", ""))}

    async def update_patient(
        self, clinic_id: str, patient_id: str, data: dict
    ) -> dict:
        result = await self._put(
            f"/facilities/{self.facility_id}/patients/{patient_id}", data
        )
        return {"patient_id": patient_id, "updated": True}

    async def get_available_slots(
        self, clinic_id: str, provider_id: str,
        date: str, reason: Optional[str] = None
    ) -> list:
        try:
            data = await self._get(
                f"/facilities/{self.facility_id}/appointments/slots",
                params={"provider_id": provider_id, "date": date},
            )
            return [
                {
                    "slot_id": str(s.get("id", "")),
                    "datetime": s.get("start_time", ""),
                    "provider_id": str(s.get("provider_id", "")),
                }
                for s in data.get("data", [])
            ]
        except Exception as e:
            logger.error("Helium get_slots failed: %s", str(e))
            return []

    async def book_appointment(
        self, clinic_id: str, patient_id: str,
        slot_id: str, reason: str
    ) -> dict:
        result = await self._post(
            f"/facilities/{self.facility_id}/appointments",
            {
                "patient_id": patient_id,
                "slot_id": slot_id,
                "reason": reason,
            },
        )
        appt = result.get("data", {})
        return {
            "appointment_id": str(appt.get("id", slot_id)),
            "status": "confirmed",
            "datetime": appt.get("start_time", ""),
            "provider": appt.get("provider_name", ""),
        }

    async def cancel_appointment(
        self, clinic_id: str, patient_id: str, appointment_id: str
    ) -> dict:
        await self._put(
            f"/facilities/{self.facility_id}/appointments/{appointment_id}/cancel",
            {"reason": "Patient request"},
        )
        return {"status": "cancelled", "appointment_id": appointment_id}

    async def _get(self, path: str, params: Optional[dict] = None) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                f"{HELIUM_BASE}{path}", params=params,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            r.raise_for_status()
            return r.json()

    async def _post(self, path: str, data: dict) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                f"{HELIUM_BASE}{path}", json=data,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            r.raise_for_status()
            return r.json()

    async def _put(self, path: str, data: dict) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.put(
                f"{HELIUM_BASE}{path}", json=data,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            r.raise_for_status()
            return r.json()
