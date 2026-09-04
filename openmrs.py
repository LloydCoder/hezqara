"""
OpenMRS EHR Client — Complete Integration.
REST API v1 — open-source, no partnership needed.
Used by hundreds of Nigerian government and NGO hospitals.
Also deployed in Kenya, Rwanda, South Africa, India, Philippines.

Auth: HTTP Basic (username:password) or session token
API:  https://{server}/openmrs/ws/rest/v1/
Docs: wiki.openmrs.org/display/docs/REST+Web+Services+API

Key endpoints:
  GET  /patient?q={name or id}     — search patients
  GET  /patient/{uuid}             — get patient
  POST /patient                    — create patient
  GET  /appointment?patient={uuid} — get appointments
  POST /appointment                — create appointment
  GET  /appointmentscheduling/slot — available slots
  GET  /encounter?patient={uuid}   — visit history

Patient identifier types (common in Nigeria):
  OpenMRS ID, NUBAN, National ID, Hospital Number

Appointment statuses:
  Scheduled, CheckedIn, Completed, Cancelled, Missed

Rate limit: none enforced by default (self-hosted)
"""
import logging
import time
from typing import Optional
import httpx

from app.ehr.base import BaseEHR

logger = logging.getLogger(__name__)

OPENMRS_TOKEN_BUFFER = 1800  # Re-auth every 30 min


class OpenMRSClient(BaseEHR):
    """
    OpenMRS REST API client.
    Works with any OpenMRS installation — Nigerian government hospitals,
    NGO clinics, MSF facilities, community health centers globally.

    Credential types:
      - Basic auth (username + password) — for self-hosted instances
      - Session token — preferred for production (avoids repeated basic auth)

    Setup:
      1. Admin creates an API user in OpenMRS admin panel
      2. Assign 'REST API' role
      3. Use those credentials here
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
    ) -> None:
        """
        base_url: OpenMRS server URL, e.g. https://openmrs.myhospital.ng/openmrs
        username: OpenMRS API user
        password: OpenMRS API password
        """
        self.base_url = base_url.rstrip("/")
        self.api_base = f"{self.base_url}/ws/rest/v1"
        self.username = username
        self.password = password
        self._session_token: Optional[str] = None
        self._token_obtained_at: float = 0.0

    # ── Authentication ────────────────────────────────────────────────────────

    async def _get_session_token(self) -> str:
        """Obtain OpenMRS session token via basic auth."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                f"{self.api_base}/session",
                auth=(self.username, self.password),
            )
            r.raise_for_status()
            data = r.json()
        self._session_token = data.get("sessionId", "")
        self._token_obtained_at = time.time()
        return self._session_token

    async def _ensure_token(self) -> str:
        """Re-authenticate if token is older than 30 minutes."""
        if (not self._session_token or
                time.time() - self._token_obtained_at > OPENMRS_TOKEN_BUFFER):
            await self._get_session_token()
        return self._session_token or ""

    async def _headers(self) -> dict:
        token = await self._ensure_token()
        return {
            "Cookie": f"JSESSIONID={token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ── Patient operations ────────────────────────────────────────────────────

    async def get_patient(self, clinic_id: str, phone: str) -> Optional[dict]:
        """
        Search patient by phone number.
        OpenMRS does not natively index by phone — searches by identifier
        or name and then filters by phone attribute.
        """
        digits = "".join(c for c in phone if c.isdigit())[-10:]
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(
                    f"{self.api_base}/patient",
                    params={"q": digits, "v": "full"},
                    headers=await self._headers(),
                )
                r.raise_for_status()
                results = r.json().get("results", [])

            for p in results:
                attrs = p.get("person", {}).get("attributes", [])
                for attr in attrs:
                    if attr.get("attributeType", {}).get("display") == "Telephone Number":
                        stored = "".join(c for c in str(attr.get("value", "")) if c.isdigit())
                        if stored.endswith(digits):
                            return self._map_patient(p)
            return None

        except Exception as e:
            logger.error("OpenMRS get_patient failed: %s", str(e))
            return None

    async def search_patient(
        self,
        clinic_id: str,
        first_name: str,
        last_name: str,
        date_of_birth: Optional[str] = None,
    ) -> Optional[dict]:
        """Search by name."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(
                    f"{self.api_base}/patient",
                    params={"q": f"{first_name} {last_name}", "v": "full"},
                    headers=await self._headers(),
                )
                r.raise_for_status()
                results = r.json().get("results", [])
            if not results:
                return None
            return self._map_patient(results[0])
        except Exception as e:
            logger.error("OpenMRS search_patient failed: %s", str(e))
            return None

    async def create_patient(self, clinic_id: str, data: dict) -> dict:
        """
        Create patient in OpenMRS.
        Generates OpenMRS ID automatically.
        """
        person = {
            "names": [{
                "givenName": data.get("first_name", ""),
                "familyName": data.get("last_name", ""),
                "preferred": True,
            }],
            "birthdate": data.get("date_of_birth", ""),
            "gender": (data.get("gender", "M") or "M")[0].upper(),
            "addresses": [],
        }

        if data.get("phone"):
            digits = "".join(c for c in data["phone"] if c.isdigit())
            person["attributes"] = [{
                "attributeType": "14d4f066-15f5-102d-96e4-000c29c2a5d7",  # Phone UUID
                "value": digits,
            }]

        body = {
            "person": person,
            "identifiers": [{
                "identifierType": "8d79403a-c2cc-11de-8d13-0010c6dffd0f",  # OpenMRS ID
                "identifier": f"CARENOVA-{data.get('first_name','').upper()[:3]}",
                "preferred": True,
            }],
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(
                    f"{self.api_base}/patient",
                    json=body,
                    headers=await self._headers(),
                )
                r.raise_for_status()
                return {"patient_id": r.json().get("uuid", "")}
        except Exception as e:
            logger.error("OpenMRS create_patient failed: %s", str(e))
            return {"patient_id": ""}

    async def update_patient(self, clinic_id: str, patient_id: str, data: dict) -> dict:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(
                    f"{self.api_base}/patient/{patient_id}",
                    json=data,
                    headers=await self._headers(),
                )
                r.raise_for_status()
                return r.json()
        except Exception as e:
            logger.error("OpenMRS update_patient failed: %s", str(e))
            return {}

    # ── Appointment operations ────────────────────────────────────────────────

    async def get_available_slots(
        self,
        clinic_id: str,
        provider_id: str,
        date: str,
        reason: Optional[str] = None,
    ) -> list:
        """
        Fetch available appointment slots.
        Uses OpenMRS Appointment Scheduling module.
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(
                    f"{self.api_base}/appointmentscheduling/slot",
                    params={
                        "appointmentType": reason or "",
                        "fromDate": f"{date}T00:00:00.000",
                        "toDate": f"{date}T23:59:59.000",
                        "includeFull": "false",
                        "v": "full",
                    },
                    headers=await self._headers(),
                )
                r.raise_for_status()
                slots = r.json().get("results", [])

            return [
                {
                    "slot_id": s.get("uuid", ""),
                    "datetime_iso": s.get("startDate", ""),
                    "datetime": s.get("startDate", ""),
                    "provider_id": provider_id,
                    "duration_minutes": (
                        s.get("appointmentBlock", {}).get("appointmentType", {}).get("duration", 20)
                    ),
                    "status": "free",
                }
                for s in slots
                if s.get("statusFull", {}).get("concept", {}).get("display") != "Booked"
            ]

        except Exception as e:
            logger.error("OpenMRS get_available_slots failed: %s", str(e))
            return []

    async def book_appointment(
        self,
        clinic_id: str,
        patient_id: str,
        slot_id: str,
        reason: str,
        appointment_type_id: Optional[str] = None,
    ) -> dict:
        """Book appointment via OpenMRS Appointment Scheduling module."""
        body = {
            "patient": patient_id,
            "timeSlot": slot_id,
            "status": "SCHEDULED",
            "reason": reason[:200] if reason else "",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(
                    f"{self.api_base}/appointmentscheduling/appointment",
                    json=body,
                    headers=await self._headers(),
                )
                r.raise_for_status()
                data = r.json()
                return {
                    "appointment_id": data.get("uuid", slot_id),
                    "status": "confirmed",
                }
        except Exception as e:
            logger.error("OpenMRS book_appointment failed: %s", str(e))
            raise

    async def cancel_appointment(
        self,
        clinic_id: str,
        patient_id: str,
        appointment_id: str,
        reason: str = "Patient request",
    ) -> dict:
        """Cancel appointment — set status to CANCELLED."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(
                    f"{self.api_base}/appointmentscheduling/appointment/{appointment_id}",
                    json={"status": "CANCELLED"},
                    headers=await self._headers(),
                )
                r.raise_for_status()
                return {"status": "cancelled", "appointment_id": appointment_id}
        except Exception as e:
            logger.error("OpenMRS cancel_appointment failed: %s", str(e))
            raise

    # ── Helper ────────────────────────────────────────────────────────────────

    def _map_patient(self, p: dict) -> dict:
        person = p.get("person", {})
        names = person.get("names", [{}])
        preferred_name = next((n for n in names if n.get("preferred")), names[0] if names else {})

        phone = ""
        for attr in person.get("attributes", []):
            if "Telephone" in attr.get("attributeType", {}).get("display", ""):
                phone = attr.get("value", "")
                break

        return {
            "patient_id": p.get("uuid", ""),
            "first_name": preferred_name.get("givenName", ""),
            "last_name": preferred_name.get("familyName", ""),
            "phone": phone,
            "date_of_birth": person.get("birthdate", ""),
            "gender": person.get("gender", "").lower(),
        }
