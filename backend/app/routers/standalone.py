"""
Standalone Mode Router — API endpoints for clinics without an EHR.
All 11 standalone modules exposed here.

POST /api/standalone/patients          — create patient
GET  /api/standalone/patients          — list patients
GET  /api/standalone/patients/{id}     — get patient
PUT  /api/standalone/patients/{id}     — update patient

GET  /api/standalone/slots             — get available slots
POST /api/standalone/appointments      — book appointment
PUT  /api/standalone/appointments/{id} — cancel appointment

POST /api/standalone/vitals            — record vitals
POST /api/standalone/notes             — save clinical note
POST /api/standalone/notes/pre-visit   — generate pre-visit draft

POST /api/standalone/import/csv        — import patients from CSV
POST /api/standalone/intake/whatsapp   — parse nurse WhatsApp message

GET  /api/standalone/providers         — list providers
POST /api/standalone/providers         — create provider

GET  /api/standalone/pricing           — pricing for clinic country
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.security.clerk_auth import extract_clinic_id as get_clinic_id
from app.standalone.patients import StandalonePatientService
from app.standalone.scheduling import StandaloneScheduler
from app.standalone.clinical import StandaloneClinicalService
from app.standalone.importer import StandaloneDataImporter
from app.standalone.whatsapp_intake import WhatsAppIntakeParser
from app.standalone.providers import StandaloneProviderService
from app.standalone.pricing import StandalonePricing
from app.standalone.manager import StandaloneManager
from app.standalone.hmo import HMOService, NHISTariff
from app.standalone.billing import PatientBillingService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/standalone", tags=["standalone"])


# ── Request / Response models ─────────────────────────────────────────────────

class CreatePatientRequest(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = "en"
    notes: Optional[str] = None

class UpdatePatientRequest(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    notes: Optional[str] = None

class BookAppointmentRequest(BaseModel):
    patient_id: str
    provider_id: str
    datetime_iso: str
    reason: str
    duration_minutes: Optional[int] = 20
    patient_phone: Optional[str] = None
    appointment_type_id: Optional[str] = None

class RecordVitalsRequest(BaseModel):
    patient_id: str
    appointment_id: str
    blood_pressure: Optional[str] = None
    temperature_celsius: Optional[float] = None
    pulse_bpm: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    spo2_percent: Optional[int] = None

class SaveNoteRequest(BaseModel):
    patient_id: str
    appointment_id: str
    soap_subjective: Optional[str] = None
    soap_objective: Optional[str] = None
    soap_assessment: Optional[str] = None
    soap_plan: Optional[str] = None

class PreVisitNoteRequest(BaseModel):
    patient_id: str
    appointment_id: str
    chief_complaint: Optional[str] = None
    current_medications: Optional[list] = None
    allergies: Optional[list] = None
    last_visit_reason: Optional[str] = None
    symptom_duration: Optional[str] = None

class CSVImportRequest(BaseModel):
    csv_content: str

class WhatsAppIntakeRequest(BaseModel):
    message: str
    nurse_phone: Optional[str] = None

class CreateProviderRequest(BaseModel):
    name: str
    specialty: Optional[str] = None
    working_hours: Optional[dict] = None
    slot_duration_minutes: Optional[int] = 20
    break_times: Optional[list] = None

class UpgradeEHRRequest(BaseModel):
    ehr_type: str
    credentials: dict

class SubmitClaimRequest(BaseModel):
    patient_id: str
    hmo_id: str
    visit_id: str
    diagnosis_code: str
    service_codes: list
    amount_ngn: float

class CreatePaymentLinkRequest(BaseModel):
    provider: str  # paystack | flutterwave
    amount_ngn: float
    patient_name: str
    patient_phone: str
    description: str
    allow_fallback: Optional[bool] = True

class RecordOfflinePaymentRequest(BaseModel):
    method: str  # cash | pos | bank_transfer
    amount_ngn: float
    patient_id: str
    visit_id: str
    received_by: str
    pos_terminal_id: Optional[str] = None


# ── Patients ──────────────────────────────────────────────────────────────────

@router.post("/patients")
async def create_patient(
    req: CreatePatientRequest,
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    svc = StandalonePatientService(clinic_id=clinic_id)
    result = await svc.create_patient(req.dict())
    return JSONResponse(content=result, status_code=201)


@router.get("/patients")
async def list_patients(
    limit: int = 100,
    offset: int = 0,
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    svc = StandalonePatientService(clinic_id=clinic_id)
    patients = await svc.get_all_patients(limit=limit, offset=offset)
    return JSONResponse(content={"patients": patients, "count": len(patients)})


@router.get("/patients/search")
async def search_patient(
    phone: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    svc = StandalonePatientService(clinic_id=clinic_id)
    if phone:
        result = await svc.find_patient_by_phone(phone)
    else:
        result = await svc.search_patient(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
        )
    if not result:
        raise HTTPException(status_code=404, detail="Patient not found")
    return JSONResponse(content=result)


@router.put("/patients/{patient_id}")
async def update_patient(
    patient_id: str,
    req: UpdatePatientRequest,
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    svc = StandalonePatientService(clinic_id=clinic_id)
    result = await svc.update_patient(
        patient_id=patient_id,
        data={k: v for k, v in req.dict().items() if v is not None},
    )
    return JSONResponse(content=result)


# ── Appointments / Scheduling ─────────────────────────────────────────────────

@router.get("/slots")
async def get_slots(
    provider_id: str,
    date: str,
    appointment_type: Optional[str] = None,
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    scheduler = StandaloneScheduler(clinic_id=clinic_id)
    slots = await scheduler.get_available_slots(
        provider_id=provider_id,
        date=date,
        appointment_type=appointment_type,
    )
    return JSONResponse(content={"slots": slots, "count": len(slots)})


@router.post("/appointments")
async def book_appointment(
    req: BookAppointmentRequest,
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    scheduler = StandaloneScheduler(clinic_id=clinic_id)
    result = await scheduler.book_appointment(
        patient_id=req.patient_id,
        provider_id=req.provider_id,
        datetime_iso=req.datetime_iso,
        reason=req.reason,
        duration_minutes=req.duration_minutes or 20,
        patient_phone=req.patient_phone,
    )
    return JSONResponse(content=result, status_code=201)


@router.put("/appointments/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: str,
    reason: str = "Patient request",
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    scheduler = StandaloneScheduler(clinic_id=clinic_id)
    result = await scheduler.cancel_appointment(
        appointment_id=appointment_id,
        reason=reason,
    )
    return JSONResponse(content=result)


# ── Clinical ──────────────────────────────────────────────────────────────────

@router.post("/vitals")
async def record_vitals(
    req: RecordVitalsRequest,
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    svc = StandaloneClinicalService(clinic_id=clinic_id)
    vitals = {k: v for k, v in req.dict().items()
              if k not in ("patient_id", "appointment_id") and v is not None}
    result = await svc.record_vitals(
        patient_id=req.patient_id,
        appointment_id=req.appointment_id,
        vitals=vitals,
    )
    return JSONResponse(content=result, status_code=201)


@router.post("/notes/pre-visit")
async def generate_pre_visit_note(
    req: PreVisitNoteRequest,
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    """
    Scribe-lite: generate draft SOAP note from intake data.
    Physician opens partially completed note — not a blank screen.
    """
    svc = StandaloneClinicalService(clinic_id=clinic_id)
    intake = {k: v for k, v in req.dict().items()
              if k not in ("patient_id", "appointment_id") and v is not None}
    result = await svc.generate_pre_visit_note(
        patient_id=req.patient_id,
        appointment_id=req.appointment_id,
        intake_data=intake,
    )
    return JSONResponse(content=result, status_code=201)


@router.post("/notes")
async def save_clinical_note(
    req: SaveNoteRequest,
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    svc = StandaloneClinicalService(clinic_id=clinic_id)
    note = {k: v for k, v in req.dict().items()
            if k not in ("patient_id", "appointment_id") and v is not None}
    result = await svc.save_clinical_note(
        patient_id=req.patient_id,
        appointment_id=req.appointment_id,
        note=note,
    )
    return JSONResponse(content=result, status_code=201)


# ── Data import ───────────────────────────────────────────────────────────────

@router.post("/import/csv")
async def import_patients_csv(
    req: CSVImportRequest,
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    """
    One-step migration from Excel/paper.
    Nurse exports Excel as CSV, uploads here.
    All patients created instantly.
    """
    importer = StandaloneDataImporter(clinic_id=clinic_id)
    result = await importer.import_patients_csv(req.csv_content)
    return JSONResponse(content=result)


# ── WhatsApp intake parser ────────────────────────────────────────────────────

@router.post("/intake/whatsapp")
async def parse_whatsapp_message(
    req: WhatsAppIntakeRequest,
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    """
    Nurse sends WhatsApp message — Carenova creates patient or books appointment.
    No computer required. Works on any phone on 2G.
    """
    parser = WhatsAppIntakeParser()
    parsed = await parser.parse_nurse_message(req.message)

    # Auto-act on parsed intent
    result = {"parsed": parsed}

    if parsed.get("intent") == "create_patient" and parsed.get("first_name"):
        svc = StandalonePatientService(clinic_id=clinic_id)
        patient = await svc.create_patient(parsed)
        result["action"] = "patient_created"
        result["patient"] = patient

    elif parsed.get("intent") == "record_vitals" and parsed.get("patient_id"):
        svc = StandaloneClinicalService(clinic_id=clinic_id)
        vitals = {k: v for k, v in parsed.items()
                  if k in ("blood_pressure", "temperature", "pulse",
                           "weight_kg", "height_cm", "spo2_percent")}
        if vitals:
            note = await svc.record_vitals(
                patient_id=parsed["patient_id"],
                appointment_id="whatsapp_intake",
                vitals=vitals,
            )
            result["action"] = "vitals_recorded"
            result["vitals"] = note

    return JSONResponse(content=result)


# ── Providers ─────────────────────────────────────────────────────────────────

@router.get("/providers")
async def list_providers(
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    svc = StandaloneProviderService(clinic_id=clinic_id)
    providers = await svc.get_all_providers()
    return JSONResponse(content={"providers": providers})


@router.post("/providers")
async def create_provider(
    req: CreateProviderRequest,
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    svc = StandaloneProviderService(clinic_id=clinic_id)
    result = await svc.create_provider(req.dict())
    return JSONResponse(content=result, status_code=201)


# ── Pricing ───────────────────────────────────────────────────────────────────

@router.get("/pricing")
async def get_pricing(country: str = "US") -> JSONResponse:
    """Returns all tier prices in local currency for a country."""
    prices = StandalonePricing.all_prices_for_country(country)
    return JSONResponse(content=prices)


# ── EHR upgrade ───────────────────────────────────────────────────────────────

@router.post("/upgrade-ehr")
async def upgrade_to_ehr(
    req: UpgradeEHRRequest,
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    """
    Upgrade standalone clinic to EHR-integrated mode.
    All historical data preserved. One settings change.
    """
    mgr = StandaloneManager(clinic_id=clinic_id)
    result = await mgr.upgrade_to_ehr(
        ehr_type=req.ehr_type,
        credentials=req.credentials,
    )
    return JSONResponse(content=result)


# ── HMO claims (Nigeria) ──────────────────────────────────────────────────────

@router.get("/hmo/directory")
async def list_hmos(clinic_id: str = Depends(get_clinic_id)) -> JSONResponse:
    """List HMOs available for patient registration and claims."""
    svc = HMOService(clinic_id=clinic_id)
    hmos = await svc.list_hmos()
    return JSONResponse(content={"hmos": hmos})


@router.get("/hmo/nhis-tariff")
async def get_nhis_tariff_codes() -> JSONResponse:
    """All NHIA tariff codes — for billing UI dropdown."""
    return JSONResponse(content={"codes": NHISTariff.get_all_codes()})


@router.post("/hmo/claims")
async def submit_hmo_claim(
    req: SubmitClaimRequest,
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    """Submit an HMO claim for a patient visit."""
    svc = HMOService(clinic_id=clinic_id)
    result = await svc.submit_claim(**req.dict())
    return JSONResponse(content=result, status_code=201)


@router.get("/hmo/claims/{claim_id}")
async def get_hmo_claim_status(
    claim_id: str,
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    """Check status of a submitted HMO claim."""
    svc = HMOService(clinic_id=clinic_id)
    result = await svc.get_claim_status(claim_id)
    return JSONResponse(content=result)


@router.get("/hmo/claims")
async def list_pending_hmo_claims(
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    """All pending HMO claims — billing dashboard."""
    svc = HMOService(clinic_id=clinic_id)
    claims = await svc.list_pending_claims()
    return JSONResponse(content={"claims": claims})


# ── Patient bill collection ───────────────────────────────────────────────────

@router.get("/billing/payment-methods")
async def get_payment_methods(
    country: str = "US",
) -> JSONResponse:
    """Available payment methods for patient bill collection, by region."""
    svc = PatientBillingService(clinic_id="", country=country)
    return JSONResponse(content={"methods": svc.get_available_payment_methods()})


@router.post("/billing/payment-link")
async def create_payment_link(
    req: CreatePaymentLinkRequest,
    country: str = "NG",
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    """Create an online payment link (Paystack or Flutterwave) for a patient bill."""
    svc = PatientBillingService(clinic_id=clinic_id, country=country)
    result = await svc.create_payment_link(**req.dict())
    return JSONResponse(content=result, status_code=201)


@router.post("/billing/offline-payment")
async def record_offline_payment(
    req: RecordOfflinePaymentRequest,
    country: str = "NG",
    clinic_id: str = Depends(get_clinic_id),
) -> JSONResponse:
    """Record a cash, POS, or bank transfer payment taken at the clinic desk."""
    svc = PatientBillingService(clinic_id=clinic_id, country=country)
    result = await svc.record_offline_payment(**req.dict())
    return JSONResponse(content=result, status_code=201)
