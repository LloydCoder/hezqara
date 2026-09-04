"""
athenahealth EHR Client — Complete Production Integration.
REST API v1 + FHIR R4 + OAuth2 with auto-refresh.

API base:
  Preview (sandbox): https://api.preview.platform.athenahealth.com/v1
  Production:        https://api.platform.athenahealth.com/v1

Token endpoint (same for both environments):
  https://api.platform.athenahealth.com/oauth2/v1/token

OAuth2 flow:
  client_credentials grant — 2-legged OAuth
  Token expires in 3600s — refreshed automatically 5 minutes before expiry
  On 401 response — force-refresh token and retry once

Key endpoints used by Carenova agents:
  GET  /{pid}/patients                    — search by phone/name/DOB
  POST /{pid}/patients                    — create patient
  PUT  /{pid}/patients/{id}               — update patient
  GET  /{pid}/appointments/open           — available slots
  PUT  /{pid}/appointments/{id}           — book appointment
  PUT  /{pid}/appointments/{id}/cancellation — cancel
  GET  /{pid}/providers                   — list providers
  GET  /{pid}/departments                 — list departments
  GET  /{pid}/appointmenttypes            — list appointment types
  POST /{pid}/patients/{id}/insurances/{iid}/eligibilitycheck — check eligibility
  POST /fhir/r4/Subscription              — subscribe to events (FHIR)

All date inputs: ISO 8601 (YYYY-MM-DD)
athenahealth date format: MM/DD/YYYY — converted internally
"""
import logging
import time
from typing import Optional
import httpx

from app.ehr.base import BaseEHR

logger = logging.getLogger(__name__)

# ── URL constants ─────────────────────────────────────────────────────────────
ATHENA_PREVIEW_BASE = "https://api.preview.platform.athenahealth.com/v1"
ATHENA_PROD_BASE    = "https://api.platform.athenahealth.com/v1"
ATHENA_FHIR_BASE    = "https://api.platform.athenahealth.com/fhir/r4"
ATHENA_TOKEN_URL    = "https://api.platform.athenahealth.com/oauth2/v1/token"

# Refresh token 5 minutes before expiry to avoid mid-call failures
TOKEN_EXPIRY_BUFFER_SECONDS = 300


class AthenaHealthClient(BaseEHR):
    """
    Complete athenahealth REST API client.
    Handles OAuth2 lifecycle, all agent operations, and error recovery.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        practice_id: str,
        base_url: str = ATHENA_PREVIEW_BASE,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.practice_id = practice_id
        self.base_url = base_url
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    # ── OAuth2 token management ───────────────────────────────────────────────

    async def _fetch_token(self) -> str:
        """
        Fetch fresh OAuth2 access token using client_credentials grant.
        Called automatically — never called by agents directly.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                ATHENA_TOKEN_URL,
                data={"grant_type": "client_credentials"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                auth=(self.client_id, self.client_secret),
            )
            r.raise_for_status()
            data = r.json()

        token = data["access_token"]
        expires_in = data.get("expires_in", 3600)

        self._access_token = token
        self._token_expires_at = time.time() + expires_in - TOKEN_EXPIRY_BUFFER_SECONDS

        logger.debug("athenahealth token refreshed, expires in %ds", expires_in)
        return token

    async def _ensure_token(self) -> str:
        """Return valid token, refreshing if expired or missing."""
        if not self._access_token or time.time() >= self._token_expires_at:
            await self._fetch_token()
        return self._access_token  # type: ignore[return-value]

    # ── Patient operations ────────────────────────────────────────────────────

    async def get_patient(self, clinic_id: str, phone: str) -> Optional[dict]:
        """Look up patient by mobile phone number."""
        digits = "".join(c for c in phone if c.isdigit())[-10:]
        try:
            data = await self._get(
                f"/{self.practice_id}/patients",
                params={"mobilephone": digits, "showallpatients": "true"},
            )
            patients = data.get("patients", [])
            if not patients:
                return None
            return self._map_patient(patients[0])
        except Exception as e:
            logger.error("get_patient failed: %s", str(e))
            return None

    async def search_patient(
        self,
        clinic_id: str,
        first_name: str,
        last_name: str,
        date_of_birth: str,
    ) -> Optional[dict]:
        """Search patient by name + DOB when phone not available."""
        try:
            data = await self._get(
                f"/{self.practice_id}/patients",
                params={
                    "firstname": first_name,
                    "lastname": last_name,
                    "dob": self._format_date(date_of_birth),
                    "showallpatients": "true",
                },
            )
            patients = data.get("patients", [])
            if not patients:
                return None
            return self._map_patient(patients[0])
        except Exception as e:
            logger.error("search_patient failed: %s", str(e))
            return None

    async def create_patient(self, clinic_id: str, data: dict) -> dict:
        """Create new patient record in athenahealth."""
        payload = {
            "firstname": data.get("first_name", ""),
            "lastname": data.get("last_name", ""),
            "dob": self._format_date(data.get("date_of_birth", "")),
            "mobilephone": "".join(c for c in data.get("phone", "") if c.isdigit())[-10:],
            "email": data.get("email", ""),
        }
        response = await self._post(f"/{self.practice_id}/patients", payload)
        if isinstance(response, list) and response:
            return {"patient_id": str(response[0].get("patientid", ""))}
        return {"patient_id": str(response.get("patientid", ""))}

    async def update_patient(
        self, clinic_id: str, patient_id: str, data: dict
    ) -> dict:
        """Update existing patient record."""
        payload = {k: v for k, v in {
            "email": data.get("email"),
            "address1": data.get("street"),
            "city": data.get("city"),
            "state": data.get("state"),
            "zip": data.get("zip"),
            "mobilephone": data.get("phone"),
        }.items() if v}
        return await self._put(
            f"/{self.practice_id}/patients/{patient_id}", payload
        )

    # ── Provider and department operations ───────────────────────────────────

    async def get_providers(self, clinic_id: str) -> list:
        """Fetch all providers — used by Scheduling Agent."""
        try:
            data = await self._get(f"/{self.practice_id}/providers")
            return [
                {
                    "provider_id": str(p.get("providerid", "")),
                    "name": f"Dr. {p.get('firstname', '')} {p.get('lastname', '')}".strip(),
                    "specialty": p.get("specialty", ""),
                    "npi": p.get("npi", ""),
                }
                for p in data.get("providers", [])
            ]
        except Exception as e:
            logger.error("get_providers failed: %s", str(e))
            return []

    async def get_departments(self, clinic_id: str) -> list:
        """Fetch departments — needed for multi-location practices."""
        try:
            data = await self._get(f"/{self.practice_id}/departments")
            return [
                {
                    "department_id": str(d.get("departmentid", "")),
                    "name": d.get("name", ""),
                    "phone": d.get("phone", ""),
                    "address": d.get("address", ""),
                }
                for d in data.get("departments", [])
            ]
        except Exception as e:
            logger.error("get_departments failed: %s", str(e))
            return []

    async def get_appointment_types(self, clinic_id: str) -> list:
        """
        Fetch valid appointment type IDs.
        Required for booking — athenahealth rejects appointments
        without a valid appointmenttypeid.
        """
        try:
            data = await self._get(f"/{self.practice_id}/appointmenttypes")
            return [
                {
                    "type_id": str(t.get("appointmenttypeid", "")),
                    "name": t.get("name", ""),
                    "duration_minutes": t.get("duration", 20),
                    "patient_facing_name": t.get("patientfacingname", t.get("name", "")),
                }
                for t in data.get("appointmenttypes", [])
            ]
        except Exception as e:
            logger.error("get_appointment_types failed: %s", str(e))
            return []

    # ── Appointment operations ────────────────────────────────────────────────

    async def get_available_slots(
        self,
        clinic_id: str,
        provider_id: str,
        date: str,
        reason: Optional[str] = None,
        appointment_type_id: str = "1",
    ) -> list:
        """Fetch open appointment slots for a provider on a given date."""
        try:
            data = await self._get(
                f"/{self.practice_id}/appointments/open",
                params={
                    "providerid": provider_id,
                    "appointmentdate": self._format_date(date),
                    "appointmenttypeid": appointment_type_id,
                    "ignoreschedulablepermission": "true",
                },
            )
            return [
                {
                    "slot_id": str(a.get("appointmentid", "")),
                    "datetime": f"{a.get('date', '')}T{a.get('starttime', '')}:00",
                    "datetime_iso": self._convert_athena_datetime(
                        a.get("date", ""), a.get("starttime", "")
                    ),
                    "provider_id": str(a.get("providerid", "")),
                    "duration_minutes": a.get("duration", 20),
                    "department_id": str(a.get("departmentid", "")),
                }
                for a in data.get("appointments", [])
            ]
        except Exception as e:
            logger.error("get_available_slots failed: %s", str(e))
            return []

    async def book_appointment(
        self,
        clinic_id: str,
        patient_id: str,
        slot_id: str,
        reason: str,
        appointment_type_id: str = "1",
    ) -> dict:
        """
        Book appointment — writes directly back to athenahealth EHR.
        This is the core value of Carenova.
        """
        response = await self._put(
            f"/{self.practice_id}/appointments/{slot_id}",
            {
                "patientid": patient_id,
                "appointmenttypeid": appointment_type_id,
                "notes": reason[:200] if reason else "",  # 200 char limit
                "bookedby": "Carenova AI",
            },
        )
        return {
            "appointment_id": str(response.get("appointmentid", slot_id)),
            "status": "confirmed",
            "datetime": response.get("date", ""),
            "provider": response.get("providername", ""),
            "department": response.get("departmentname", ""),
        }

    async def cancel_appointment(
        self,
        clinic_id: str,
        patient_id: str,
        appointment_id: str,
        reason: str = "Patient request",
    ) -> dict:
        """Cancel appointment and free the slot."""
        await self._put(
            f"/{self.practice_id}/appointments/{appointment_id}/cancellation",
            {
                "patientid": patient_id,
                "cancellationreason": reason,
                "ignoreschedulablepermission": "true",
            },
        )
        return {"status": "cancelled", "appointment_id": appointment_id}

    # ── Insurance eligibility ─────────────────────────────────────────────────

    async def check_eligibility(
        self,
        clinic_id: str,
        patient_id: str,
        insurance_id: str,
        date_of_service: str,
    ) -> dict:
        """
        Real-time insurance eligibility check via athenahealth.
        Returns copay, deductible remaining, and eligibility status.
        Failure returns eligible=None (unknown) — never blocks the call.
        """
        try:
            response = await self._post(
                f"/{self.practice_id}/patients/{patient_id}/insurances/{insurance_id}/eligibilitycheck",
                {"servicedate": self._format_date(date_of_service)},
            )

            status = response.get("eligibilitystatus", "")
            eligible = status.lower() == "active" if status else None

            # Parse copay
            copay = None
            for c in response.get("copays", []):
                if c.get("copaytype") == "PRIMARY_CARE":
                    try:
                        copay = float(c.get("amount", "0").replace("$", ""))
                    except ValueError:
                        pass

            # Parse deductible remaining
            deductible_remaining = None
            for d in response.get("deductibles", []):
                try:
                    deductible_remaining = float(
                        str(d.get("remaining", "0")).replace("$", "").replace(",", "")
                    )
                    break
                except ValueError:
                    pass

            return {
                "eligible": eligible,
                "status": status,
                "carrier": response.get("insurancepolicyholderid", ""),
                "copay_primary_care": copay,
                "deductible_remaining": deductible_remaining,
                "insurance_id": insurance_id,
            }

        except Exception as e:
            logger.warning("eligibility check failed for patient %s: %s", patient_id, str(e))
            return {
                "eligible": None,  # Unknown — not a hard failure
                "error": str(e),
                "insurance_id": insurance_id,
            }

    # ── FHIR R4 event subscriptions ──────────────────────────────────────────

    async def subscribe_to_events(
        self,
        event_type: str,
        callback_url: str,
        webhook_secret: str,
        practice_ids: Optional[list] = None,
    ) -> dict:
        """
        Subscribe to athenahealth FHIR R4 event notifications.
        Receives real-time updates when appointments change in EHR.
        Requires special scope — request from athenahealth API team.
        """
        pids = practice_ids or [self.practice_id]
        filter_criteria = [
            f"ah-practice=Organization/a-1.Practice-{pid}" for pid in pids
        ]

        subscription_body = {
            "resourceType": "Subscription",
            "status": "requested",
            "reason": "Carenova AI — real-time EHR sync",
            "criteria": f"https://api.platform.athenahealth.com/fhir/r4/SubscriptionTopic/{event_type}.update",
            "_criteria": {
                "extension": [
                    {
                        "url": "http://hl7.org/fhir/uv/subscriptions-backport/StructureDefinition/backport-filter-criteria",
                        "valueString": fc,
                    }
                    for fc in filter_criteria
                ]
            },
            "channel": {
                "type": "rest-hook",
                "endpoint": callback_url,
                "header": [f"X-Hub-Secret: {webhook_secret}"],
            },
        }

        response = await self._post_fhir("/Subscription", subscription_body)
        return {
            "subscription_id": response.get("id", ""),
            "status": response.get("status", ""),
            "event_type": event_type,
        }

    # ── Private HTTP helpers ──────────────────────────────────────────────────

    async def _get(self, path: str, params: Optional[dict] = None) -> dict:
        """GET request with automatic token management and 401 retry."""
        return await self._request("GET", path, params=params)

    async def _post(self, path: str, data: dict) -> dict:
        """POST request with form-encoded body (athenahealth standard)."""
        return await self._request("POST", path, form_data=data)

    async def _put(self, path: str, data: dict) -> dict:
        """PUT request with form-encoded body."""
        return await self._request("PUT", path, form_data=data)

    async def _post_fhir(self, path: str, json_data: dict) -> dict:
        """POST to FHIR R4 endpoints (JSON body, different base URL)."""
        token = await self._ensure_token()
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                f"{ATHENA_FHIR_BASE}{path}",
                json=json_data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/fhir+json",
                },
            )
            r.raise_for_status()
            return r.json()

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        form_data: Optional[dict] = None,
        _retry: bool = True,
    ) -> dict:
        """
        Core HTTP request with:
        - Automatic token refresh before expiry
        - Single retry on 401 (token may have been revoked)
        - Request-ID header for athenahealth tracing
        """
        token = await self._ensure_token()
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Request-Id": f"carenova-{id(self)}-{int(time.time())}",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                if method == "GET":
                    r = await client.get(url, params=params, headers=headers)
                elif method == "POST":
                    r = await client.post(url, data=form_data, headers=headers)
                elif method == "PUT":
                    r = await client.put(url, data=form_data, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                # 401 — token may have been revoked. Refresh once and retry.
                if r.status_code == 401 and _retry:
                    logger.warning("athenahealth 401 — refreshing token and retrying")
                    self._access_token = None
                    self._token_expires_at = 0.0
                    return await self._request(
                        method, path, params=params,
                        form_data=form_data, _retry=False
                    )

                r.raise_for_status()
                return r.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("athenahealth rate limited (429) on %s", path)
            raise

    # ── Utility helpers ───────────────────────────────────────────────────────

    def _format_date(self, iso_date: str) -> str:
        """Convert YYYY-MM-DD → MM/DD/YYYY for athenahealth."""
        if not iso_date:
            return ""
        parts = iso_date.split("-")
        if len(parts) == 3:
            return f"{parts[1]}/{parts[2]}/{parts[0]}"
        return iso_date

    def _convert_athena_datetime(self, athena_date: str, start_time: str) -> str:
        """Convert athenahealth date + time to ISO 8601."""
        if not athena_date or not start_time:
            return ""
        # athena_date: MM/DD/YYYY, start_time: HH:MM
        parts = athena_date.split("/")
        if len(parts) == 3:
            return f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}T{start_time}:00"
        return f"{athena_date}T{start_time}:00"

    def _map_patient(self, p: dict) -> dict:
        """Map athenahealth patient dict to Carenova internal format."""
        return {
            "patient_id": str(p.get("patientid", "")),
            "first_name": p.get("firstname", ""),
            "last_name": p.get("lastname", ""),
            "phone": p.get("mobilephone", ""),
            "email": p.get("email", ""),
            "date_of_birth": self._athena_date_to_iso(p.get("dob", "")),
        }

    def _athena_date_to_iso(self, athena_date: str) -> str:
        """Convert MM/DD/YYYY → YYYY-MM-DD."""
        if not athena_date:
            return ""
        parts = athena_date.split("/")
        if len(parts) == 3:
            return f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
        return athena_date
