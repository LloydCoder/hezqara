"""
Cerner (Oracle Health) EHR Client.
Your aunt's federal hospital is transitioning to Cerner.

Auth: SMART on FHIR — authorization_code OR client_credentials
API:  FHIR R4 — same pattern as Epic
Docs: docs.oracle.com/en-us/iaas/Content/dev-ops/health.htm
      fhir.cerner.com

Key facts:
  - Each Cerner tenant has a unique FHIR endpoint
  - Millennium (hospital) vs Ambulatory EHR (clinic) — same API
  - Ignite APIs: additional Cerner-proprietary endpoints
  - Token endpoint: https://authorization.cerner.com/tenants/{tenant_id}/protocols/oauth2/profiles/smart-v1/token
  - Federal hospitals use DSTU2 or R4 depending on version

Oracle Health Marketplace:
  Apply at: marketplace.oracle.com/health
  Takes: 2-3 months for approval
  Apply now — runs in parallel to building
"""
import logging
import time
from typing import Optional
import httpx

from app.ehr.base import BaseEHR

logger = logging.getLogger(__name__)

CERNER_TOKEN_BASE   = "https://authorization.cerner.com/tenants"
CERNER_FHIR_SANDBOX = "https://fhir-ehr-code.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d"
CERNER_TOKEN_EXPIRY_BUFFER = 300


class CernerClient(BaseEHR):
    """
    Cerner (Oracle Health) EHR client.
    FHIR R4 via SMART on FHIR authorization.

    For federal hospitals (your aunt's):
      - Tenant ID provided by hospital IT during onboarding
      - FHIR endpoint unique per institution
      - May require separate approval from hospital administration

    Timeline:
      - Apply to Oracle Health Marketplace now
      - Target: ready when hospital completes Cerner transition
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: str,
        fhir_base_url: str = CERNER_FHIR_SANDBOX,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.fhir_base_url = fhir_base_url
        self.token_url = (
            f"{CERNER_TOKEN_BASE}/{tenant_id}"
            "/protocols/oauth2/profiles/smart-v1/token"
        )
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    async def _fetch_token(self) -> str:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "system/Patient.read system/Appointment.read system/Appointment.write",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            r.raise_for_status()
            data = r.json()
        self._access_token = data["access_token"]
        self._token_expires_at = (
            time.time() + data.get("expires_in", 3600) - CERNER_TOKEN_EXPIRY_BUFFER
        )
        return self._access_token

    async def _ensure_token(self) -> str:
        if not self._access_token or time.time() >= self._token_expires_at:
            await self._fetch_token()
        return self._access_token  # type: ignore[return-value]

    async def _headers(self) -> dict:
        token = await self._ensure_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json",
        }

    async def get_patient(self, clinic_id: str, phone: str) -> Optional[dict]:
        digits = "".join(c for c in phone if c.isdigit())[-10:]
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.get(
                    f"{self.fhir_base_url}/Patient",
                    params={"telecom": f"phone|{digits}"},
                    headers=await self._headers(),
                )
                r.raise_for_status()
                entries = r.json().get("entry", [])
            if not entries:
                return None
            p = entries[0]["resource"]
            name = (p.get("name") or [{}])[0]
            return {
                "patient_id": p.get("id", ""),
                "first_name": (name.get("given") or [""])[0],
                "last_name": name.get("family", ""),
                "phone": phone,
                "date_of_birth": p.get("birthDate", ""),
            }
        except Exception as e:
            logger.error("Cerner get_patient failed: %s", str(e))
            return None

    async def create_patient(self, clinic_id: str, data: dict) -> dict:
        body = {
            "resourceType": "Patient",
            "name": [{"family": data.get("last_name",""), "given": [data.get("first_name","")]}],
            "birthDate": data.get("date_of_birth", ""),
            "telecom": [{"system": "phone", "value": data.get("phone", "")}],
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.post(f"{self.fhir_base_url}/Patient",
                                 json=body, headers=await self._headers())
                r.raise_for_status()
                return {"patient_id": r.json().get("id", "")}
        except Exception as e:
            logger.error("Cerner create_patient failed: %s", str(e))
            return {"patient_id": ""}

    async def update_patient(self, clinic_id: str, patient_id: str, data: dict) -> dict:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.put(
                    f"{self.fhir_base_url}/Patient/{patient_id}",
                    json={"resourceType": "Patient", "id": patient_id},
                    headers=await self._headers(),
                )
                r.raise_for_status()
                return r.json()
        except Exception as e:
            logger.error("Cerner update_patient failed: %s", str(e))
            return {}

    async def get_available_slots(
        self, clinic_id: str, provider_id: str, date: str, reason: Optional[str] = None
    ) -> list:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.get(
                    f"{self.fhir_base_url}/Slot",
                    params={"schedule.actor": f"Practitioner/{provider_id}",
                            "start": f"ge{date}", "status": "free"},
                    headers=await self._headers(),
                )
                r.raise_for_status()
                return [{"slot_id": e["resource"]["id"],
                         "datetime_iso": e["resource"].get("start",""),
                         "datetime": e["resource"].get("start",""),
                         "provider_id": provider_id}
                        for e in r.json().get("entry", [])]
        except Exception as e:
            logger.error("Cerner get_available_slots failed: %s", str(e))
            return []

    async def book_appointment(
        self, clinic_id: str, patient_id: str, slot_id: str, reason: str
    ) -> dict:
        body = {
            "resourceType": "Appointment",
            "status": "booked",
            "description": reason[:500],
            "participant": [
                {"actor": {"reference": f"Patient/{patient_id}"}, "status": "accepted"}
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.post(f"{self.fhir_base_url}/Appointment",
                                 json=body, headers=await self._headers())
                r.raise_for_status()
                return {"appointment_id": r.json().get("id",""), "status": "confirmed"}
        except Exception as e:
            logger.error("Cerner book_appointment failed: %s", str(e))
            raise

    async def cancel_appointment(
        self, clinic_id: str, patient_id: str, appointment_id: str
    ) -> dict:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.put(
                    f"{self.fhir_base_url}/Appointment/{appointment_id}",
                    json={"resourceType":"Appointment","id":appointment_id,"status":"cancelled"},
                    headers=await self._headers(),
                )
                r.raise_for_status()
                return {"status": "cancelled", "appointment_id": appointment_id}
        except Exception as e:
            logger.error("Cerner cancel_appointment failed: %s", str(e))
            raise
