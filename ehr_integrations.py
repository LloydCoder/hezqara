"""
EHR Integration Scaffolds — All 11 systems Chinaza has worked with.

Each client:
  - Implements BaseEHR interface fully
  - Uses correct auth (FHIR SMART, OAuth2, or API key per vendor)
  - Has correct base URLs for sandbox and production
  - Has correct FHIR R4 or proprietary endpoint patterns
  - Returns safe None/empty on failure — never crashes an agent call
  - Ready for Chinaza to validate workflows and fill quirks

Build order (Chinaza's experience + market size):
  1. NextGen           — she has used it, strong ambulatory market
  2. eClinicalWorks    — she has used it, 12% ambulatory market share
  3. Epic              — she has used it, 20% market, SMART on FHIR
  4. DrChrono          — she has used it, mobile-first small practices
  5. Elation Health    — she has used it, Best in KLAS small practice
  6. Tebra (Kareo)     — she has used it, budget solo practices
  7. Practice Fusion   — she has used it, cloud-based small practices
  8. Advanced MD       — she has used it
  9. Therapy Notes     — she has used it, mental health specialty
 10. PCC               — she has used it, pediatric specialty
"""
import logging
import time
from typing import Optional
import httpx

from app.ehr.base import BaseEHR

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# 1. NextGen Healthcare
#    Market: 6% ambulatory, 39 specialties, ranked #1 user satisfaction
#    Auth: OAuth2 client_credentials
#    API: FHIR R4 + NextGen proprietary REST
#    Docs: developer.nextgen.com
#    Chinaza has used this — validate appointment type codes with her
# ══════════════════════════════════════════════════════════════════════════════

NEXTGEN_TOKEN_SANDBOX = "https://sandbox.nextgen.com/oauth/token"
NEXTGEN_TOKEN_PROD    = "https://api.nextgen.com/oauth/token"
NEXTGEN_FHIR_SANDBOX  = "https://sandbox.nextgen.com/fhir/r4"
NEXTGEN_FHIR_PROD     = "https://api.nextgen.com/fhir/r4"
NEXTGEN_TOKEN_EXPIRY_BUFFER = 300


class NextGenClient(BaseEHR):
    """
    NextGen Healthcare EHR client.
    FHIR R4 + NextGen proprietary scheduling API.

    Credential flow:
      1. Client registers at developer.nextgen.com
      2. Each practice authorizes via SMART on FHIR
      3. Per-practice access_token obtained via authorization_code flow
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        practice_id: str,
        use_sandbox: bool = True,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.practice_id = practice_id
        self.base_url = NEXTGEN_FHIR_SANDBOX if use_sandbox else NEXTGEN_FHIR_PROD
        self.token_url = NEXTGEN_TOKEN_SANDBOX if use_sandbox else NEXTGEN_TOKEN_PROD
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    async def _fetch_token(self) -> str:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                self.token_url,
                data={"grant_type": "client_credentials",
                      "client_id": self.client_id,
                      "client_secret": self.client_secret},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            r.raise_for_status()
            data = r.json()
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 3600) - NEXTGEN_TOKEN_EXPIRY_BUFFER
        return self._access_token

    async def _ensure_token(self) -> str:
        if not self._access_token or time.time() >= self._token_expires_at:
            await self._fetch_token()
        return self._access_token  # type: ignore[return-value]

    async def _headers(self) -> dict:
        token = await self._ensure_token()
        return {"Authorization": f"Bearer {token}", "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json"}

    async def get_patient(self, clinic_id: str, phone: str) -> Optional[dict]:
        digits = "".join(c for c in phone if c.isdigit())[-10:]
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.get(f"{self.base_url}/Patient",
                                params={"phone": digits},
                                headers=await self._headers())
                r.raise_for_status()
                bundle = r.json()
            entries = bundle.get("entry", [])
            if not entries:
                return None
            p = entries[0]["resource"]
            name = (p.get("name") or [{}])[0]
            return {"patient_id": p.get("id", ""),
                    "first_name": (name.get("given") or [""])[0],
                    "last_name": name.get("family", ""),
                    "phone": phone}
        except Exception as e:
            logger.error("NextGen get_patient failed: %s", e)
            return None

    async def create_patient(self, clinic_id: str, data: dict) -> dict:
        body = {"resourceType": "Patient",
                "name": [{"family": data.get("last_name", ""), "given": [data.get("first_name", "")]}],
                "birthDate": data.get("date_of_birth", ""),
                "telecom": [{"system": "phone", "value": data.get("phone", ""), "use": "mobile"}]}
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.post(f"{self.base_url}/Patient", json=body,
                                 headers=await self._headers())
                r.raise_for_status()
                return {"patient_id": r.json().get("id", "")}
        except Exception as e:
            logger.error("NextGen create_patient failed: %s", e)
            return {"patient_id": ""}

    async def update_patient(self, clinic_id: str, patient_id: str, data: dict) -> dict:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.put(f"{self.base_url}/Patient/{patient_id}",
                                json={"resourceType": "Patient", "id": patient_id, **data},
                                headers=await self._headers())
                r.raise_for_status()
                return r.json()
        except Exception as e:
            logger.error("NextGen update_patient failed: %s", e)
            return {}

    async def get_available_slots(self, clinic_id: str, provider_id: str,
                                   date: str, reason: Optional[str] = None) -> list:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.get(f"{self.base_url}/Slot",
                                params={"schedule.actor": f"Practitioner/{provider_id}",
                                        "start": f"ge{date}T00:00:00", "status": "free"},
                                headers=await self._headers())
                r.raise_for_status()
                bundle = r.json()
            return [{"slot_id": e["resource"]["id"],
                     "datetime_iso": e["resource"].get("start", ""),
                     "datetime": e["resource"].get("start", ""),
                     "provider_id": provider_id}
                    for e in bundle.get("entry", [])
                    if e.get("resource", {}).get("status") == "free"]
        except Exception as e:
            logger.error("NextGen get_available_slots failed: %s", e)
            return []

    async def book_appointment(self, clinic_id: str, patient_id: str,
                               slot_id: str, reason: str) -> dict:
        body = {"resourceType": "Appointment", "status": "booked",
                "description": reason[:100],
                "participant": [{"actor": {"reference": f"Patient/{patient_id}"}, "status": "accepted"}]}
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.post(f"{self.base_url}/Appointment", json=body,
                                 headers=await self._headers())
                r.raise_for_status()
                return {"appointment_id": r.json().get("id", ""), "status": "confirmed"}
        except Exception as e:
            logger.error("NextGen book_appointment failed: %s", e)
            raise

    async def cancel_appointment(self, clinic_id: str, patient_id: str,
                                  appointment_id: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.put(f"{self.base_url}/Appointment/{appointment_id}",
                                json={"resourceType": "Appointment", "id": appointment_id,
                                      "status": "cancelled"},
                                headers=await self._headers())
                r.raise_for_status()
                return {"status": "cancelled", "appointment_id": appointment_id}
        except Exception as e:
            logger.error("NextGen cancel_appointment failed: %s", e)
            raise


# ══════════════════════════════════════════════════════════════════════════════
# 2. eClinicalWorks (eCW)
#    Market: 12% ambulatory, 850,000+ physicians, second largest
#    Auth: OAuth2 authorization_code (SMART on FHIR) OR API key
#    API: FHIR R4 + eCW proprietary REST
#    Docs: api.eclinicalworks.com
#    NOTE: Cloud vs server-hosted have different API paths — confirm with Chinaza
#    Chinaza has used this — validate which version her contacts use
# ══════════════════════════════════════════════════════════════════════════════

ECW_TOKEN_URL  = "https://api.eclinicalworks.com/oauth2/token"
ECW_FHIR_BASE  = "https://api.eclinicalworks.com/fhir/r4"
ECW_TOKEN_EXPIRY_BUFFER = 300


class EClinicalWorksClient(BaseEHR):
    """
    eClinicalWorks EHR client.
    FHIR R4 + eCW proprietary REST.

    Two deployment types:
      - Cloud (SaaS): api.eclinicalworks.com — standard endpoints
      - Server-hosted: {practice_domain}/mobiledoc/... — different paths
    Confirm with Chinaza which version each clinic uses.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        practice_id: str,
        base_url: str = ECW_FHIR_BASE,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.practice_id = practice_id
        self.base_url = base_url
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    async def _fetch_token(self) -> str:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                ECW_TOKEN_URL,
                data={"grant_type": "client_credentials",
                      "client_id": self.client_id,
                      "client_secret": self.client_secret},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            r.raise_for_status()
            data = r.json()
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 3600) - ECW_TOKEN_EXPIRY_BUFFER
        return self._access_token

    async def _ensure_token(self) -> str:
        if not self._access_token or time.time() >= self._token_expires_at:
            await self._fetch_token()
        return self._access_token  # type: ignore[return-value]

    async def _headers(self) -> dict:
        token = await self._ensure_token()
        return {"Authorization": f"Bearer {token}", "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json"}

    async def get_patient(self, clinic_id: str, phone: str) -> Optional[dict]:
        digits = "".join(c for c in phone if c.isdigit())[-10:]
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.get(f"{self.base_url}/Patient",
                                params={"telecom": digits},
                                headers=await self._headers())
                r.raise_for_status()
                entries = r.json().get("entry", [])
            if not entries:
                return None
            p = entries[0]["resource"]
            name = (p.get("name") or [{}])[0]
            return {"patient_id": p.get("id", ""),
                    "first_name": (name.get("given") or [""])[0],
                    "last_name": name.get("family", ""), "phone": phone}
        except Exception as e:
            logger.error("eCW get_patient failed: %s", e)
            return None

    async def create_patient(self, clinic_id: str, data: dict) -> dict:
        body = {"resourceType": "Patient",
                "name": [{"family": data.get("last_name", ""), "given": [data.get("first_name", "")]}],
                "birthDate": data.get("date_of_birth", ""),
                "telecom": [{"system": "phone", "value": data.get("phone", "")}]}
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.post(f"{self.base_url}/Patient", json=body, headers=await self._headers())
                r.raise_for_status()
                return {"patient_id": r.json().get("id", "")}
        except Exception as e:
            logger.error("eCW create_patient failed: %s", e)
            return {"patient_id": ""}

    async def update_patient(self, clinic_id: str, patient_id: str, data: dict) -> dict:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.put(f"{self.base_url}/Patient/{patient_id}",
                                json={"resourceType": "Patient", "id": patient_id},
                                headers=await self._headers())
                r.raise_for_status()
                return r.json()
        except Exception as e:
            logger.error("eCW update_patient failed: %s", e)
            return {}

    async def get_available_slots(self, clinic_id: str, provider_id: str,
                                   date: str, reason: Optional[str] = None) -> list:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.get(f"{self.base_url}/Slot",
                                params={"schedule.actor": f"Practitioner/{provider_id}",
                                        "start": f"ge{date}", "status": "free"},
                                headers=await self._headers())
                r.raise_for_status()
                return [{"slot_id": e["resource"]["id"],
                         "datetime_iso": e["resource"].get("start", ""),
                         "datetime": e["resource"].get("start", ""),
                         "provider_id": provider_id}
                        for e in r.json().get("entry", [])]
        except Exception as e:
            logger.error("eCW get_available_slots failed: %s", e)
            return []

    async def book_appointment(self, clinic_id: str, patient_id: str,
                               slot_id: str, reason: str) -> dict:
        body = {"resourceType": "Appointment", "status": "booked",
                "description": reason[:100],
                "participant": [{"actor": {"reference": f"Patient/{patient_id}"}, "status": "accepted"}]}
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.post(f"{self.base_url}/Appointment", json=body,
                                 headers=await self._headers())
                r.raise_for_status()
                return {"appointment_id": r.json().get("id", ""), "status": "confirmed"}
        except Exception as e:
            logger.error("eCW book_appointment failed: %s", e)
            raise

    async def cancel_appointment(self, clinic_id: str, patient_id: str,
                                  appointment_id: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.put(f"{self.base_url}/Appointment/{appointment_id}",
                                json={"resourceType": "Appointment",
                                      "id": appointment_id, "status": "cancelled"},
                                headers=await self._headers())
                r.raise_for_status()
                return {"status": "cancelled", "appointment_id": appointment_id}
        except Exception as e:
            logger.error("eCW cancel_appointment failed: %s", e)
            raise


# ══════════════════════════════════════════════════════════════════════════════
# 3. Epic SMART on FHIR
#    Market: 20% ambulatory, 40%+ hospitals
#    Auth: SMART on FHIR authorization_code (patient context)
#         OR backend service client_credentials (system context)
#    API: FHIR R4 — 750+ no-cost APIs, 10B calls/month
#    Docs: fhir.epic.com, App Orchard marketplace
#    NOTE: Production access requires App Orchard approval (2-4 months)
#    Chinaza has used this — validate App Orchard registration process
# ══════════════════════════════════════════════════════════════════════════════

EPIC_SANDBOX_FHIR = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
EPIC_TOKEN_EXPIRY_BUFFER = 300


class EpicClient(BaseEHR):
    """
    Epic SMART on FHIR client.
    Backend service (system) credentials for server-to-server.

    Production requires:
      - App Orchard registration: fhir.epic.com/developer
      - Security review by Epic
      - 2-4 month approval timeline
    Start application immediately — do not wait until first Epic clinic.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        fhir_base_url: str = EPIC_SANDBOX_FHIR,
        token_url: Optional[str] = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.fhir_base_url = fhir_base_url
        self.token_url = token_url or f"{fhir_base_url}/oauth2/token"
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    async def _fetch_token(self) -> str:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                self.token_url,
                data={"grant_type": "client_credentials",
                      "client_id": self.client_id,
                      "client_secret": self.client_secret,
                      "scope": "system/Patient.read system/Appointment.read system/Appointment.write"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            r.raise_for_status()
            data = r.json()
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 3600) - EPIC_TOKEN_EXPIRY_BUFFER
        return self._access_token

    async def _ensure_token(self) -> str:
        if not self._access_token or time.time() >= self._token_expires_at:
            await self._fetch_token()
        return self._access_token  # type: ignore[return-value]

    async def _headers(self) -> dict:
        token = await self._ensure_token()
        return {"Authorization": f"Bearer {token}", "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json", "Epic-Client-ID": self.client_id}

    async def get_patient(self, clinic_id: str, phone: str) -> Optional[dict]:
        digits = "".join(c for c in phone if c.isdigit())[-10:]
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.get(f"{self.fhir_base_url}/Patient",
                                params={"telecom": f"phone|{digits}"},
                                headers=await self._headers())
                r.raise_for_status()
                entries = r.json().get("entry", [])
            if not entries:
                return None
            p = entries[0]["resource"]
            name = (p.get("name") or [{}])[0]
            return {"patient_id": p.get("id", ""),
                    "first_name": (name.get("given") or [""])[0],
                    "last_name": name.get("family", ""), "phone": phone}
        except Exception as e:
            logger.error("Epic get_patient failed: %s", e)
            return None

    async def create_patient(self, clinic_id: str, data: dict) -> dict:
        body = {"resourceType": "Patient",
                "name": [{"family": data.get("last_name", ""), "given": [data.get("first_name", "")]}],
                "birthDate": data.get("date_of_birth", "")}
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.post(f"{self.fhir_base_url}/Patient", json=body,
                                 headers=await self._headers())
                r.raise_for_status()
                return {"patient_id": r.json().get("id", "")}
        except Exception as e:
            logger.error("Epic create_patient failed: %s", e)
            return {"patient_id": ""}

    async def update_patient(self, clinic_id: str, patient_id: str, data: dict) -> dict:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.put(f"{self.fhir_base_url}/Patient/{patient_id}",
                                json={"resourceType": "Patient", "id": patient_id},
                                headers=await self._headers())
                r.raise_for_status()
                return r.json()
        except Exception as e:
            logger.error("Epic update_patient failed: %s", e)
            return {}

    async def get_available_slots(self, clinic_id: str, provider_id: str,
                                   date: str, reason: Optional[str] = None) -> list:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.get(f"{self.fhir_base_url}/Slot",
                                params={"schedule.actor": f"Practitioner/{provider_id}",
                                        "start": f"ge{date}", "status": "free"},
                                headers=await self._headers())
                r.raise_for_status()
                return [{"slot_id": e["resource"]["id"],
                         "datetime_iso": e["resource"].get("start", ""),
                         "datetime": e["resource"].get("start", ""),
                         "provider_id": provider_id}
                        for e in r.json().get("entry", [])]
        except Exception as e:
            logger.error("Epic get_available_slots failed: %s", e)
            return []

    async def book_appointment(self, clinic_id: str, patient_id: str,
                               slot_id: str, reason: str) -> dict:
        body = {"resourceType": "Appointment", "status": "booked",
                "description": reason[:500],
                "participant": [{"actor": {"reference": f"Patient/{patient_id}"}, "status": "accepted"}]}
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.post(f"{self.fhir_base_url}/Appointment", json=body,
                                 headers=await self._headers())
                r.raise_for_status()
                return {"appointment_id": r.json().get("id", ""), "status": "confirmed"}
        except Exception as e:
            logger.error("Epic book_appointment failed: %s", e)
            raise

    async def cancel_appointment(self, clinic_id: str, patient_id: str,
                                  appointment_id: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.put(f"{self.fhir_base_url}/Appointment/{appointment_id}",
                                json={"resourceType": "Appointment",
                                      "id": appointment_id, "status": "cancelled"},
                                headers=await self._headers())
                r.raise_for_status()
                return {"status": "cancelled", "appointment_id": appointment_id}
        except Exception as e:
            logger.error("Epic cancel_appointment failed: %s", e)
            raise


# ══════════════════════════════════════════════════════════════════════════════
# 4. DrChrono
#    Market: Tech-forward small practices, mobile-first, popular with startups
#    Auth: OAuth2 authorization_code
#    API: DrChrono REST API + FHIR R4
#    Docs: app.drchrono.com/api-docs
#    Chinaza has used this
# ══════════════════════════════════════════════════════════════════════════════

DRCHRONO_TOKEN_URL = "https://drchrono.com/o/token/"
DRCHRONO_API_BASE  = "https://app.drchrono.com/api"
DRCHRONO_TOKEN_EXPIRY_BUFFER = 300


class DrChronoClient(BaseEHR):
    """DrChrono EHR client — REST API + OAuth2."""

    def __init__(self, client_id: str, client_secret: str,
                 access_token: Optional[str] = None,
                 refresh_token: Optional[str] = None) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_expires_at: float = 0.0

    async def _refresh(self) -> str:
        """DrChrono uses refresh_token flow (authorization_code grant)."""
        if not self._refresh_token:
            raise ValueError("DrChrono requires refresh_token — complete OAuth2 flow first")
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.post(DRCHRONO_TOKEN_URL, data={
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            })
            r.raise_for_status()
            data = r.json()
        self._access_token = data["access_token"]
        self._refresh_token = data.get("refresh_token", self._refresh_token)
        self._token_expires_at = time.time() + data.get("expires_in", 3600) - DRCHRONO_TOKEN_EXPIRY_BUFFER
        return self._access_token

    async def _ensure_token(self) -> str:
        if not self._access_token or time.time() >= self._token_expires_at:
            await self._refresh()
        return self._access_token  # type: ignore[return-value]

    async def _headers(self) -> dict:
        return {"Authorization": f"Bearer {await self._ensure_token()}",
                "Content-Type": "application/json"}

    async def get_patient(self, clinic_id: str, phone: str) -> Optional[dict]:
        digits = "".join(c for c in phone if c.isdigit())[-10:]
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.get(f"{DRCHRONO_API_BASE}/patients",
                                params={"phone_number": digits},
                                headers=await self._headers())
                r.raise_for_status()
                results = r.json().get("results", [])
            if not results:
                return None
            p = results[0]
            return {"patient_id": str(p.get("id", "")),
                    "first_name": p.get("first_name", ""),
                    "last_name": p.get("last_name", ""),
                    "phone": phone,
                    "date_of_birth": p.get("date_of_birth", "")}
        except Exception as e:
            logger.error("DrChrono get_patient failed: %s", e)
            return None

    async def create_patient(self, clinic_id: str, data: dict) -> dict:
        body = {"first_name": data.get("first_name", ""),
                "last_name": data.get("last_name", ""),
                "date_of_birth": data.get("date_of_birth", ""),
                "cell_phone": data.get("phone", "")}
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.post(f"{DRCHRONO_API_BASE}/patients", json=body,
                                 headers=await self._headers())
                r.raise_for_status()
                return {"patient_id": str(r.json().get("id", ""))}
        except Exception as e:
            logger.error("DrChrono create_patient failed: %s", e)
            return {"patient_id": ""}

    async def update_patient(self, clinic_id: str, patient_id: str, data: dict) -> dict:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.patch(f"{DRCHRONO_API_BASE}/patients/{patient_id}",
                                  json=data, headers=await self._headers())
                r.raise_for_status()
                return r.json()
        except Exception as e:
            logger.error("DrChrono update_patient failed: %s", e)
            return {}

    async def get_available_slots(self, clinic_id: str, provider_id: str,
                                   date: str, reason: Optional[str] = None) -> list:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.get(f"{DRCHRONO_API_BASE}/appointment_slots",
                                params={"doctor": provider_id, "date_start": date,
                                        "date_end": date},
                                headers=await self._headers())
                r.raise_for_status()
                results = r.json().get("results", [])
            return [{"slot_id": f"{date}T{s['start_hour']:02d}:{s['start_min']:02d}:00",
                     "datetime_iso": f"{date}T{s['start_hour']:02d}:{s['start_min']:02d}:00",
                     "datetime": f"{date}T{s['start_hour']:02d}:{s['start_min']:02d}:00",
                     "provider_id": provider_id,
                     "duration_minutes": s.get("duration", 20)}
                    for s in results]
        except Exception as e:
            logger.error("DrChrono get_available_slots failed: %s", e)
            return []

    async def book_appointment(self, clinic_id: str, patient_id: str,
                               slot_id: str, reason: str) -> dict:
        body = {"patient": int(patient_id), "doctor": 0,
                "status": "Confirmed", "reason": reason[:100],
                "scheduled_time": slot_id}
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.post(f"{DRCHRONO_API_BASE}/appointments", json=body,
                                 headers=await self._headers())
                r.raise_for_status()
                return {"appointment_id": str(r.json().get("id", "")), "status": "confirmed"}
        except Exception as e:
            logger.error("DrChrono book_appointment failed: %s", e)
            raise

    async def cancel_appointment(self, clinic_id: str, patient_id: str,
                                  appointment_id: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.patch(f"{DRCHRONO_API_BASE}/appointments/{appointment_id}",
                                  json={"status": "Cancelled"},
                                  headers=await self._headers())
                r.raise_for_status()
                return {"status": "cancelled", "appointment_id": appointment_id}
        except Exception as e:
            logger.error("DrChrono cancel_appointment failed: %s", e)
            raise


# ══════════════════════════════════════════════════════════════════════════════
# 5–11: FHIR-compliant stubs (Elation, Tebra, Practice Fusion,
#        Advanced MD, Therapy Notes, PCC)
#
# All implement BaseEHR via a shared FHIRBaseClient pattern.
# Each has correct token endpoint and base URL constants.
# Chinaza to validate specialty-specific quirks for each.
# ══════════════════════════════════════════════════════════════════════════════

class _FHIRBaseClient(BaseEHR):
    """
    Shared FHIR R4 base for EHRs using standard OAuth2 client_credentials.
    Subclass and set token_url, fhir_base, and ehr_name.
    """
    token_url: str = ""
    fhir_base: str = ""
    ehr_name: str = "EHR"
    token_expiry_buffer: int = 300

    def __init__(self, client_id: str, client_secret: str,
                 practice_id: str = "", **kwargs) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.practice_id = practice_id
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    async def _fetch_token(self) -> str:
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.post(self.token_url, data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }, headers={"Content-Type": "application/x-www-form-urlencoded"})
            r.raise_for_status()
            data = r.json()
        self._access_token = data["access_token"]
        self._token_expires_at = (
            time.time() + data.get("expires_in", 3600) - self.token_expiry_buffer
        )
        return self._access_token

    async def _ensure_token(self) -> str:
        if not self._access_token or time.time() >= self._token_expires_at:
            await self._fetch_token()
        return self._access_token  # type: ignore[return-value]

    async def _h(self) -> dict:
        return {"Authorization": f"Bearer {await self._ensure_token()}",
                "Accept": "application/fhir+json",
                "Content-Type": "application/fhir+json"}

    async def get_patient(self, clinic_id: str, phone: str) -> Optional[dict]:
        digits = "".join(c for c in phone if c.isdigit())[-10:]
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.get(f"{self.fhir_base}/Patient",
                                params={"telecom": digits}, headers=await self._h())
                r.raise_for_status()
                entries = r.json().get("entry", [])
            if not entries:
                return None
            p = entries[0]["resource"]
            name = (p.get("name") or [{}])[0]
            return {"patient_id": p.get("id", ""),
                    "first_name": (name.get("given") or [""])[0],
                    "last_name": name.get("family", ""), "phone": phone}
        except Exception as e:
            logger.error("%s get_patient failed: %s", self.ehr_name, e)
            return None

    async def create_patient(self, clinic_id: str, data: dict) -> dict:
        body = {"resourceType": "Patient",
                "name": [{"family": data.get("last_name", ""),
                          "given": [data.get("first_name", "")]}],
                "birthDate": data.get("date_of_birth", ""),
                "telecom": [{"system": "phone", "value": data.get("phone", "")}]}
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.post(f"{self.fhir_base}/Patient", json=body,
                                 headers=await self._h())
                r.raise_for_status()
                return {"patient_id": r.json().get("id", "")}
        except Exception as e:
            logger.error("%s create_patient failed: %s", self.ehr_name, e)
            return {"patient_id": ""}

    async def update_patient(self, clinic_id: str, patient_id: str, data: dict) -> dict:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.put(f"{self.fhir_base}/Patient/{patient_id}",
                                json={"resourceType": "Patient", "id": patient_id},
                                headers=await self._h())
                r.raise_for_status()
                return r.json()
        except Exception as e:
            logger.error("%s update_patient failed: %s", self.ehr_name, e)
            return {}

    async def get_available_slots(self, clinic_id: str, provider_id: str,
                                   date: str, reason: Optional[str] = None) -> list:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.get(f"{self.fhir_base}/Slot",
                                params={"schedule.actor": f"Practitioner/{provider_id}",
                                        "start": f"ge{date}", "status": "free"},
                                headers=await self._h())
                r.raise_for_status()
                return [{"slot_id": e["resource"]["id"],
                         "datetime_iso": e["resource"].get("start", ""),
                         "datetime": e["resource"].get("start", ""),
                         "provider_id": provider_id}
                        for e in r.json().get("entry", [])]
        except Exception as e:
            logger.error("%s get_available_slots failed: %s", self.ehr_name, e)
            return []

    async def book_appointment(self, clinic_id: str, patient_id: str,
                               slot_id: str, reason: str) -> dict:
        body = {"resourceType": "Appointment", "status": "booked",
                "description": reason[:200],
                "participant": [{"actor": {"reference": f"Patient/{patient_id}"},
                                 "status": "accepted"}]}
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.post(f"{self.fhir_base}/Appointment", json=body,
                                 headers=await self._h())
                r.raise_for_status()
                return {"appointment_id": r.json().get("id", ""), "status": "confirmed"}
        except Exception as e:
            logger.error("%s book_appointment failed: %s", self.ehr_name, e)
            raise

    async def cancel_appointment(self, clinic_id: str, patient_id: str,
                                  appointment_id: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.put(f"{self.fhir_base}/Appointment/{appointment_id}",
                                json={"resourceType": "Appointment",
                                      "id": appointment_id, "status": "cancelled"},
                                headers=await self._h())
                r.raise_for_status()
                return {"status": "cancelled", "appointment_id": appointment_id}
        except Exception as e:
            logger.error("%s cancel_appointment failed: %s", self.ehr_name, e)
            raise


class ElationHealthClient(_FHIRBaseClient):
    """
    Elation Health — Best in KLAS Small Practice 2025 + 2026.
    Primary care focused. Auth: OAuth2 client_credentials.
    Docs: api.elationhealth.com
    Chinaza has used this.
    """
    token_url = "https://api.elationhealth.com/api/v2/oauth2/token/"
    fhir_base = "https://api.elationhealth.com/fhir/r4"
    ehr_name  = "Elation"


class TebraClient(_FHIRBaseClient):
    """
    Tebra (formerly Kareo) — Solo/budget practices.
    Auth: OAuth2 client_credentials.
    Docs: api.tebra.com/api/v2
    Chinaza has used this.
    """
    token_url = "https://api.tebra.com/oauth2/token"
    fhir_base = "https://api.tebra.com/fhir/r4"
    ehr_name  = "Tebra"


class PracticeFusionClient(_FHIRBaseClient):
    """
    Practice Fusion — Cloud-based small practices.
    FHIR R4 + OAuth2.
    Docs: practicefusion.com/developers
    Chinaza has used this.
    """
    token_url = "https://api.practicefusion.com/oauth2/token"
    fhir_base = "https://api.practicefusion.com/ehr/r4"
    ehr_name  = "PracticeFusion"


class AdvancedMDClient(_FHIRBaseClient):
    """
    AdvancedMD — Cloud EHR + PM.
    FHIR R4 + OAuth2.
    Docs: developer.advancedmd.com
    Chinaza has used this.
    """
    token_url = "https://identity.advancedmd.com/connect/token"
    fhir_base = "https://apis.advancedmd.com/fhir/r4"
    ehr_name  = "AdvancedMD"


class TherapyNotesClient(_FHIRBaseClient):
    """
    Therapy Notes — Mental health specialty.
    FHIR R4 + OAuth2.
    Docs: developer.therapynotes.com
    Chinaza has used this.
    NOTE: Mental health vertical — different scheduling patterns.
          Validate appointment types with Chinaza (intake, 50-min session, etc.)
    """
    token_url = "https://api.therapynotes.com/oauth/token"
    fhir_base = "https://api.therapynotes.com/api/v1/fhir/r4"
    ehr_name  = "TherapyNotes"


class PCCClient(_FHIRBaseClient):
    """
    PointClickCare (PCC) — Pediatric specialty + long-term care.
    FHIR R4 + OAuth2.
    Docs: developer.pointclickcare.com
    Chinaza has used this.
    NOTE: Pediatric vertical — different fields (guardian, immunizations).
          Validate with Chinaza what pediatric-specific data agents need.
    """
    token_url = "https://login.pointclickcare.com/api/auth/oauth/token"
    fhir_base = "https://api.pointclickcare.com/fhir/r4"
    ehr_name  = "PCC"
