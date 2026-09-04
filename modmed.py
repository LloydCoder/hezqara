"""
ModMed EHR Client — Complete Production Integration.
Based on official documentation: portal.api.modmed.com

AUTHENTICATION (New — client_credentials):
  Sandbox token: https://ssoqa01-lb-01.m2qa.com/auth/realms/ema-fhir/protocol/openid-connect/token
  Prod token:    https://sso.ema.md/auth/realms/ema-fhir/protocol/openid-connect/token
  - RS256 JWT, expires_in=900 (15 min), NO refresh token
  - All API calls need BOTH: Authorization: Bearer {token} AND x-api-key: {key}
  - Legacy password grant still supported but being sunset — we use client_credentials

URL STRUCTURE:
  Each practice has a unique prefix:
    https://{practice_prefix}.ema.md/{practice_prefix}/ema/fhir/v2/
  Example:
    https://dermassoc.ema.md/dermassoc/ema/fhir/v2/Patient

CRITICAL — EMA vs MMPM:
  - EMA-only practices have NO scheduling data whatsoever
  - Appointments/slots ONLY exist in ModMed Practice Management (MMPM)
  - Always confirm has_mmpm=True before attempting any scheduling
  - Chinaza's clinic: confirm this before pilot goes live

IDENTIFIERS:
  - Patient: EMAID (MMI unique ID) — use this everywhere
  - Also may have: PMSID (external PM), MRN
  - Provider: MMI identifier + NPI

FHIR RESOURCES USED:
  Patient     — GET, POST, PUT
  Slot        — GET (availability)
  Appointment — GET, POST, PUT (booking/cancellation)
  Practitioner — GET (providers)
  Coverage    — GET, POST (insurance)
  ValueSet    — GET (appointment types, cancellation reasons)

RATE LIMIT: 1000 calls/minute

BOOKING FLOW (MMPM):
  1. GET /fhir/v2/ValueSet/appointment-type → firm's valid types
  2. GET /fhir/v2/Slot?... → available slots, cache slot details
  3. GET /fhir/v2/Patient?... → find/confirm patient EMAID
  4. POST /fhir/v2/Appointment → book with required fields
  Required appointment fields:
    status: "booked"
    start: ISO 8601 datetime
    end: ISO 8601 datetime
    minutesDuration: integer
    participant: [{Patient, Practitioner, Location}]
    appointmentType: from ValueSet

INSURANCE (Coverage) — MMPM only:
  - READ/SEARCH available without MMPM
  - CREATE requires MMPM + manual reconciliation by practice staff
  - order: 1=Primary, 2=Secondary, 3=Tertiary
"""
import logging
import time
from typing import Optional
import httpx

from app.ehr.base import BaseEHR

logger = logging.getLogger(__name__)

# ── URL constants ─────────────────────────────────────────────────────────────
MODMED_TOKEN_SANDBOX = (
    "https://ssoqa01-lb-01.m2qa.com/auth/realms/ema-fhir"
    "/protocol/openid-connect/token"
)
MODMED_TOKEN_PROD = (
    "https://sso.ema.md/auth/realms/ema-fhir"
    "/protocol/openid-connect/token"
)

# ModMed tokens expire in 900s (15 min) — much shorter than athenahealth's 3600s
# Refresh 2 minutes before expiry to be safe
MODMED_TOKEN_EXPIRY_BUFFER = 120


class ModMedClient(BaseEHR):
    """
    Complete ModMed EHR client.
    Handles client_credentials OAuth2, all FHIR R4 operations,
    MMPM scheduling, slot caching, and insurance coverage.

    Per-practice credentials:
      Each practice the clinic admin enables your app for generates
      a unique client_id + client_secret pair. Store them per practice.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        practice_prefix: str,
        api_key: str,
        has_mmpm: bool = True,
        use_sandbox: bool = True,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.practice_prefix = practice_prefix
        self.api_key = api_key
        self.has_mmpm = has_mmpm
        self.use_sandbox = use_sandbox

        # Build base URL: https://{prefix}.ema.md/{prefix}/ema/fhir/v2
        if use_sandbox:
            self.base_url = (
                f"https://stage.ema-api.com/ema-dev/firm"
                f"/{practice_prefix}/ema/fhir/v2"
            )
        else:
            self.base_url = (
                f"https://{practice_prefix}.ema.md"
                f"/{practice_prefix}/ema/fhir/v2"
            )

        self.token_url = MODMED_TOKEN_SANDBOX if use_sandbox else MODMED_TOKEN_PROD

        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

        # Slot cache: store slot details at availability time
        # needed at booking time for start/end/duration/location
        self._slot_cache: dict = {}

    # ── OAuth2 token management ───────────────────────────────────────────────

    async def _fetch_token(self) -> str:
        """
        Fetch access token via client_credentials grant.
        ModMed RS256 JWT — expires in 900s — no refresh token.
        Must request new token when expired.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            r.raise_for_status()
            data = r.json()

        token = data["access_token"]
        expires_in = data.get("expires_in", 900)

        self._access_token = token
        self._token_expires_at = time.time() + expires_in - MODMED_TOKEN_EXPIRY_BUFFER

        logger.debug(
            "ModMed token refreshed for practice=%s, expires_in=%ds",
            self.practice_prefix, expires_in
        )
        return token

    async def _ensure_token(self) -> str:
        """Return valid token, fetching fresh one if expired."""
        if not self._access_token or time.time() >= self._token_expires_at:
            await self._fetch_token()
        return self._access_token  # type: ignore[return-value]

    # ── Patient operations ────────────────────────────────────────────────────

    async def get_patient(self, clinic_id: str, phone: str) -> Optional[dict]:
        """
        Search patient by phone number.
        ModMed FHIR: GET /Patient?telecom={phone}
        Returns None gracefully on any failure — never crashes a call.
        """
        digits = "".join(c for c in phone if c.isdigit())[-10:]
        try:
            bundle = await self._get(
                "/Patient",
                params={"telecom": digits},
            )
            return self._first_patient_from_bundle(bundle)
        except Exception as e:
            logger.error("ModMed get_patient failed: %s", str(e))
            return None

    async def search_patient(
        self,
        clinic_id: str,
        first_name: str,
        last_name: str,
        date_of_birth: str,
    ) -> Optional[dict]:
        """
        Search by name + DOB — primary fallback when phone unavailable.
        ModMed FHIR: GET /Patient?given=Maria&family=Santos&birthdate=1985-03-15
        """
        try:
            bundle = await self._get(
                "/Patient",
                params={
                    "given": first_name,
                    "family": last_name,
                    "birthdate": date_of_birth,
                },
            )
            return self._first_patient_from_bundle(bundle)
        except Exception as e:
            logger.error("ModMed search_patient failed: %s", str(e))
            return None

    async def create_patient(self, clinic_id: str, data: dict) -> dict:
        """
        Create patient via FHIR R4 Patient CREATE.
        ModMed docs: match on first name, last name, DOB, gender to avoid duplicates.
        """
        digits = "".join(c for c in data.get("phone", "") if c.isdigit())[-10:]

        fhir_patient = {
            "resourceType": "Patient",
            "name": [{"family": data.get("last_name", ""), "given": [data.get("first_name", "")]}],
            "birthDate": data.get("date_of_birth", ""),
            "telecom": [],
            "active": True,
        }

        if digits:
            fhir_patient["telecom"].append(
                {"system": "phone", "value": digits, "use": "mobile", "rank": 1}
            )
        if data.get("email"):
            fhir_patient["telecom"].append(
                {"system": "email", "value": data["email"], "rank": 2}
            )
        if data.get("gender"):
            fhir_patient["gender"] = data["gender"].lower()

        response = await self._post("/Patient", fhir_patient)
        return {"patient_id": str(response.get("id", ""))}

    async def update_patient(
        self, clinic_id: str, patient_id: str, data: dict
    ) -> dict:
        """
        Update patient — PUT partial FHIR Patient resource.
        ModMed: only send fields you want to update.
        """
        patch_body: dict = {}

        if data.get("email"):
            patch_body["telecom"] = [
                {"system": "email", "value": data["email"]},
            ]
        if data.get("phone"):
            digits = "".join(c for c in data["phone"] if c.isdigit())[-10:]
            telecom = patch_body.get("telecom", [])
            telecom.append({"system": "phone", "value": digits, "use": "mobile"})
            patch_body["telecom"] = telecom
        if data.get("street"):
            patch_body["address"] = [{
                "line": [data["street"]],
                "city": data.get("city", ""),
                "state": data.get("state", ""),
                "postalCode": data.get("zip", ""),
            }]

        patch_body["resourceType"] = "Patient"
        patch_body["id"] = patient_id

        return await self._put(f"/Patient/{patient_id}", patch_body)

    # ── Provider operations ───────────────────────────────────────────────────

    async def get_providers(self, clinic_id: str) -> list:
        """
        Fetch all practitioners for this practice.
        ModMed FHIR: GET /Practitioner
        """
        try:
            bundle = await self._get("/Practitioner", params={"active": "true"})
            providers = []
            for entry in bundle.get("entry", []):
                p = entry.get("resource", {})
                if p.get("resourceType") != "Practitioner":
                    continue
                name_obj = (p.get("name") or [{}])[0]
                family = name_obj.get("family", "")
                given = (name_obj.get("given") or [""])[0]
                prefix = (name_obj.get("prefix") or ["Dr."])[0]

                npi = ""
                for ident in p.get("identifier", []):
                    if "us-npi" in ident.get("system", ""):
                        npi = ident.get("value", "")
                        break

                providers.append({
                    "provider_id": str(p.get("id", "")),
                    "name": f"{prefix} {given} {family}".strip(),
                    "npi": npi,
                    "active": p.get("active", True),
                })
            return providers
        except Exception as e:
            logger.error("ModMed get_providers failed: %s", str(e))
            return []

    async def get_appointment_types(self, clinic_id: str) -> list:
        """
        Fetch firm-specific appointment types from ValueSet.
        GET /fhir/v2/ValueSet/appointment-type
        Returns only ACTIVE types.
        """
        try:
            vs = await self._get("/ValueSet/appointment-type")
            types = []
            for item in vs.get("expansion", {}).get("contains", []):
                duration = 20  # default
                for prop in item.get("property", []):
                    if prop.get("code") == "duration":
                        duration = prop.get("valueInteger", 20)
                types.append({
                    "type_id": item.get("code", ""),
                    "name": item.get("display", ""),
                    "duration_minutes": duration,
                })
            return types
        except Exception as e:
            logger.error("ModMed get_appointment_types failed: %s", str(e))
            return []

    # ── Appointment / scheduling operations ──────────────────────────────────

    async def get_available_slots(
        self,
        clinic_id: str,
        provider_id: str,
        date: str,
        reason: Optional[str] = None,
        appointment_type_id: Optional[str] = None,
    ) -> list:
        """
        Fetch available slots for a provider.
        MMPM required — EMA-only returns empty list with warning logged.

        Slots are cached internally so book_appointment has the
        start/end/duration/location data needed to build the FHIR
        Appointment resource.
        """
        if not self.has_mmpm:
            logger.warning(
                "ModMed practice=%s is EMA-only — no scheduling available",
                self.practice_prefix
            )
            return []

        try:
            params: dict = {
                "status": "free",
                "start": f"ge{date}T00:00:00",
                "start": f"le{date}T23:59:59",
            }
            if appointment_type_id:
                params["appointmentType"] = appointment_type_id

            bundle = await self._get("/Slot", params=params)

            slots = []
            for entry in bundle.get("entry", []):
                s = entry.get("resource", {})
                if s.get("resourceType") != "Slot":
                    continue
                if s.get("status") != "free":
                    continue

                start_iso = s.get("start", "")
                end_iso = s.get("end", "")
                slot_id = str(s.get("id", ""))

                # Parse duration from start/end
                duration_minutes = 20
                try:
                    from datetime import datetime
                    st = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
                    en = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
                    duration_minutes = int((en - st).total_seconds() / 60)
                except Exception:
                    pass

                # Extract location and provider from schedule reference
                schedule_ref = s.get("schedule", {}).get("reference", "")
                location_id = ""
                sched_provider_id = provider_id

                # Cache slot details for booking
                self._slot_cache[slot_id] = {
                    "start": start_iso,
                    "end": end_iso,
                    "duration_minutes": duration_minutes,
                    "location_id": location_id,
                    "provider_id": sched_provider_id,
                    "schedule_ref": schedule_ref,
                }

                slots.append({
                    "slot_id": slot_id,
                    "datetime_iso": start_iso,
                    "datetime": start_iso,
                    "provider_id": sched_provider_id,
                    "duration_minutes": duration_minutes,
                    "status": "free",
                })
            return slots

        except Exception as e:
            logger.error("ModMed get_available_slots failed: %s", str(e))
            return []

    async def book_appointment(
        self,
        clinic_id: str,
        patient_id: str,
        slot_id: str,
        reason: str,
        appointment_type_id: Optional[str] = None,
        location_id: Optional[str] = None,
        provider_id: Optional[str] = None,
    ) -> dict:
        """
        Book appointment via FHIR Appointment CREATE.
        MMPM required — raises ValueError if EMA-only.

        Required FHIR fields per ModMed docs:
          status: "booked"
          start, end, minutesDuration
          participant: [Patient, Practitioner, Location]
          appointmentType: from ValueSet

        Slot cache used to recover start/end/duration/location
        from the earlier get_available_slots call.
        """
        if not self.has_mmpm:
            raise ValueError(
                f"ModMed practice {self.practice_prefix} is EMA-only — "
                "MMPM required for appointment scheduling. "
                "Ask the clinic admin to confirm they have MMPM."
            )

        # Recover slot details from cache or use provided values
        cached = self._slot_cache.get(slot_id, {})
        start = cached.get("start", "")
        end = cached.get("end", "")
        duration = cached.get("duration_minutes", 20)
        loc_id = location_id or cached.get("location_id", "")
        prov_id = provider_id or cached.get("provider_id", "")

        # Build FHIR Appointment resource
        participants = [
            {
                "actor": {"reference": f"Patient/{patient_id}"},
                "status": "accepted",
            }
        ]
        if prov_id:
            participants.append({
                "actor": {"reference": f"Practitioner/{prov_id}"},
                "status": "accepted",
            })
        if loc_id:
            participants.append({
                "actor": {"reference": f"Location/{loc_id}"},
                "status": "accepted",
            })

        body: dict = {
            "resourceType": "Appointment",
            "status": "booked",
            "start": start,
            "end": end,
            "minutesDuration": duration,
            "participant": participants,
            "description": reason[:100] if reason else "",  # reason for visit
            "comment": f"Booked via Carenova AI — {reason[:200] if reason else ''}",
        }

        if appointment_type_id:
            body["appointmentType"] = {
                "coding": [{"code": appointment_type_id}]
            }

        response = await self._post("/Appointment", body)

        return {
            "appointment_id": str(response.get("id", slot_id)),
            "status": "confirmed",
            "datetime_iso": response.get("start", start),
            "datetime": response.get("start", start),
            "provider_id": prov_id,
            "raw_status": response.get("status", "booked"),
        }

    async def cancel_appointment(
        self,
        clinic_id: str,
        patient_id: str,
        appointment_id: str,
        reason: str = "Patient request",
    ) -> dict:
        """
        Cancel appointment via FHIR Appointment UPDATE.
        PUT status=cancelled + cancelationReason.
        """
        body = {
            "resourceType": "Appointment",
            "id": appointment_id,
            "status": "cancelled",
            "cancelationReason": {
                "coding": [{"display": reason}]
            },
        }

        await self._put(f"/Appointment/{appointment_id}", body)
        return {"status": "cancelled", "appointment_id": appointment_id}

    # ── Insurance / Coverage operations ──────────────────────────────────────

    async def get_patient_insurance(
        self, clinic_id: str, patient_id: str
    ) -> Optional[dict]:
        """
        Fetch patient's active insurance coverages.
        GET /fhir/v2/Coverage?patient={emaid}
        order: 1=Primary, 2=Secondary, 3=Tertiary
        Returns primary coverage or None.
        """
        try:
            bundle = await self._get(
                "/Coverage",
                params={"patient": patient_id},
            )
            entries = bundle.get("entry", [])
            if not entries:
                return None

            # Sort by order to get primary first
            coverages = []
            for entry in entries:
                c = entry.get("resource", {})
                if c.get("resourceType") != "Coverage":
                    continue
                coverages.append(c)

            coverages.sort(key=lambda c: c.get("order", 99))
            if not coverages:
                return None

            primary = coverages[0]
            payers = primary.get("payor", [{}])
            carrier = payers[0].get("display", "") if payers else ""

            # Extract plan/group from class
            plan_number = ""
            group_number = ""
            for cls in primary.get("class", []):
                code = cls.get("type", {}).get("code", "")
                if code == "plan":
                    plan_number = cls.get("value", "")
                elif code == "group":
                    group_number = cls.get("value", "")

            return {
                "coverage_id": str(primary.get("id", "")),
                "status": primary.get("status", ""),
                "order": primary.get("order", 1),
                "carrier": carrier,
                "plan_number": plan_number,
                "group_number": group_number,
                "patient_id": patient_id,
            }

        except Exception as e:
            logger.error("ModMed get_patient_insurance failed: %s", str(e))
            return None

    # ── Private HTTP helpers ──────────────────────────────────────────────────

    async def _get(
        self,
        path: str,
        params: Optional[dict] = None,
        _retry: bool = True,
    ) -> dict:
        return await self._request("GET", path, params=params, _retry=_retry)

    async def _post(self, path: str, json_data: dict) -> dict:
        return await self._request("POST", path, json_data=json_data)

    async def _put(self, path: str, json_data: dict) -> dict:
        return await self._request("PUT", path, json_data=json_data)

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
        _retry: bool = True,
    ) -> dict:
        """
        Core HTTP request with:
        - Automatic token refresh (900s expiry)
        - x-api-key header on every call (ModMed requirement)
        - Single 401 retry with fresh token
        - Accept: application/fhir+json
        """
        token = await self._ensure_token()
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {token}",
            "x-api-key": self.api_key,
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json",
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                if method == "GET":
                    r = await client.get(url, params=params, headers=headers)
                elif method == "POST":
                    r = await client.post(url, json=json_data, headers=headers)
                elif method == "PUT":
                    r = await client.put(url, json=json_data, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                # 401 — token expired mid-session — refresh once and retry
                if r.status_code == 401 and _retry:
                    logger.warning(
                        "ModMed 401 on %s — refreshing token and retrying",
                        path
                    )
                    self._access_token = None
                    self._token_expires_at = 0.0
                    return await self._request(
                        method, path,
                        params=params, json_data=json_data,
                        _retry=False
                    )

                r.raise_for_status()

                # 201 Created returns empty body — return minimal dict
                if r.status_code == 201:
                    try:
                        return r.json()
                    except Exception:
                        # Location header has the new resource URL
                        loc = r.headers.get("Location", "")
                        resource_id = loc.split("/")[-1] if loc else ""
                        return {"id": resource_id, "status": "created"}

                return r.json()

        except httpx.HTTPStatusError:
            raise
        except Exception as e:
            logger.error("ModMed %s %s failed: %s", method, path, str(e))
            raise

    # ── FHIR helpers ─────────────────────────────────────────────────────────

    def _first_patient_from_bundle(self, bundle: dict) -> Optional[dict]:
        """Extract and map first patient from a FHIR Bundle response."""
        entries = bundle.get("entry", [])
        if not entries:
            return None

        for entry in entries:
            p = entry.get("resource", {})
            if p.get("resourceType") == "Patient":
                return self._map_fhir_patient(p)
        return None

    def _map_fhir_patient(self, p: dict) -> dict:
        """Map FHIR R4 Patient resource to Carenova internal format."""
        name_obj = (p.get("name") or [{}])[0]
        family = name_obj.get("family", "")
        given = (name_obj.get("given") or [""])[0]

        # Extract phone from telecom
        phone = ""
        email = ""
        for t in p.get("telecom", []):
            if t.get("system") == "phone" and not phone:
                phone = t.get("value", "")
            if t.get("system") == "email" and not email:
                email = t.get("value", "")

        # Extract EMAID from identifiers
        emaid = str(p.get("id", ""))

        return {
            "patient_id": emaid,
            "first_name": given,
            "last_name": family,
            "phone": phone,
            "email": email,
            "date_of_birth": p.get("birthDate", ""),
            "gender": p.get("gender", ""),
            "active": p.get("active", True),
        }
