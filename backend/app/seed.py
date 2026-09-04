"""
Demo Seed Data — Carenova AI
Realistic family medicine clinic data for demos and onboarding.
Covers US (Family Care Associates) and Nigeria (Owerri Family Clinic).

Run: python -m app.demo.seed
Or:  POST /api/demo/seed  (admin only)
"""
import uuid
from datetime import datetime, date, timedelta

# ── US Demo Clinic ────────────────────────────────────────────────────────────
US_CLINIC = {
    "id": "demo_clinic_us",
    "name": "Family Care Associates",
    "ehr_type": "athenahealth",
    "ehr_practice_id": "195900",
    "phone_number": "+18885550001",
    "timezone": "America/New_York",
    "country": "US",
    "plan_tier": "pro",
    "whatsapp_enabled": False,
    "hipaa_baa_signed": True,
    "active_agents": [
        "reception", "scheduling", "intake", "insurance",
        "prior_auth", "refill", "records", "referrals", "recall", "email"
    ],
}

# ── Nigeria Demo Clinic ───────────────────────────────────────────────────────
NG_CLINIC = {
    "id": "demo_clinic_ng",
    "name": "Owerri Family Clinic",
    "ehr_type": "standalone",
    "phone_number": "+2348031000001",
    "timezone": "Africa/Lagos",
    "country": "NG",
    "plan_tier": "pro",
    "whatsapp_enabled": True,
    "hipaa_baa_signed": False,
    "active_agents": [
        "reception", "scheduling", "intake", "refill", "recall"
    ],
}

# ── US Providers ──────────────────────────────────────────────────────────────
US_PROVIDERS = [
    {"id": "prov_chen",    "name": "Dr. James Chen",    "specialty": "Family Medicine",  "npi": "1234567890"},
    {"id": "prov_kim",     "name": "Dr. Sarah Kim",     "specialty": "Internal Medicine","npi": "0987654321"},
    {"id": "prov_adeyemi", "name": "Dr. Ngozi Adeyemi", "specialty": "Family Medicine",  "npi": "1122334455"},
]

NG_PROVIDERS = [
    {"id": "prov_chukwu",  "name": "Dr. Chukwu Emeka", "specialty": "Family Medicine"},
    {"id": "prov_okafor",  "name": "Dr. Okafor Ifeoma","specialty": "Pediatrics"},
]

# ── US Patients ───────────────────────────────────────────────────────────────
US_PATIENTS = [
    {
        "id": "pat_maria",
        "first_name": "Maria", "last_name": "Santos",
        "date_of_birth": "1985-03-15", "gender": "female",
        "phone": "+12125551234", "email": "maria.santos@email.com",
        "insurance_carrier": "BlueCross BlueShield",
        "insurance_member_id": "BCB-847291",
        "insurance_group": "GRP-001",
    },
    {
        "id": "pat_james",
        "first_name": "James", "last_name": "Mitchell",
        "date_of_birth": "1972-11-08", "gender": "male",
        "phone": "+19175555678", "email": "james.m@email.com",
        "insurance_carrier": "Aetna",
        "insurance_member_id": "AET-123456",
        "insurance_group": "GRP-002",
    },
    {
        "id": "pat_priya",
        "first_name": "Priya", "last_name": "Sharma",
        "date_of_birth": "1990-07-22", "gender": "female",
        "phone": "+16465559012", "email": "priya.sharma@email.com",
        "insurance_carrier": "United Healthcare",
        "insurance_member_id": "UHC-789012",
        "insurance_group": "GRP-003",
    },
    {
        "id": "pat_robert",
        "first_name": "Robert", "last_name": "Chen",
        "date_of_birth": "1965-04-30", "gender": "male",
        "phone": "+17185553456", "email": "robert.chen@email.com",
        "insurance_carrier": "Medicare",
        "insurance_member_id": "MED-345678",
        "uninsured": False,
    },
    {
        "id": "pat_angela",
        "first_name": "Angela", "last_name": "White",
        "date_of_birth": "1978-09-12", "gender": "female",
        "phone": "+12015557890", "email": "angela.w@email.com",
        "insurance_carrier": "Cigna",
        "insurance_member_id": "CIG-567890",
        "insurance_group": "GRP-004",
    },
]

# ── Nigeria Patients ──────────────────────────────────────────────────────────
NG_PATIENTS = [
    {
        "id": "pat_amaka",
        "first_name": "Amaka", "last_name": "Obi",
        "date_of_birth": "1990-03-15", "gender": "female",
        "phone": "+2348031234567",
        "insurance_carrier": "NHIS",
        "language": "ig",
    },
    {
        "id": "pat_chukwu",
        "first_name": "Chukwuemeka", "last_name": "Nwosu",
        "date_of_birth": "1978-11-22", "gender": "male",
        "phone": "+2347012345678",
        "uninsured": True,
        "language": "ig",
    },
    {
        "id": "pat_ngozi",
        "first_name": "Ngozi", "last_name": "Adeyemi",
        "date_of_birth": "1982-06-04", "gender": "female",
        "phone": "+2348098765432",
        "insurance_carrier": "Hygeia",
        "language": "yo",
    },
]

# ── US Appointments — today ───────────────────────────────────────────────────
today = date.today().isoformat()

US_APPOINTMENTS = [
    {
        "id": "appt_001",
        "patient_id": "pat_maria",
        "provider_id": "prov_chen",
        "provider_name": "Dr. James Chen",
        "appointment_datetime": f"{today}T09:00:00",
        "duration_minutes": 45,
        "reason": "Annual physical exam",
        "status": "confirmed",
        "booked_by_agent": "scheduling",
        "ehr_appointment_id": "APT-ATHENA-8291",
    },
    {
        "id": "appt_002",
        "patient_id": "pat_james",
        "provider_id": "prov_kim",
        "provider_name": "Dr. Sarah Kim",
        "appointment_datetime": f"{today}T10:30:00",
        "duration_minutes": 20,
        "reason": "Follow-up — hypertension management",
        "status": "scheduled",
        "booked_by_agent": "scheduling",
    },
    {
        "id": "appt_003",
        "patient_id": "pat_priya",
        "provider_id": "prov_chen",
        "provider_name": "Dr. James Chen",
        "appointment_datetime": f"{today}T11:00:00",
        "duration_minutes": 60,
        "reason": "New patient — comprehensive intake",
        "status": "confirmed",
        "booked_by_agent": "scheduling",
    },
    {
        "id": "appt_004",
        "patient_id": "pat_robert",
        "provider_id": "prov_kim",
        "provider_name": "Dr. Sarah Kim",
        "appointment_datetime": f"{today}T14:00:00",
        "duration_minutes": 30,
        "reason": "Diabetes checkup — A1C review",
        "status": "scheduled",
        "booked_by_agent": "scheduling",
    },
    {
        "id": "appt_005",
        "patient_id": "pat_angela",
        "provider_id": "prov_adeyemi",
        "provider_name": "Dr. Ngozi Adeyemi",
        "appointment_datetime": f"{today}T15:30:00",
        "duration_minutes": 20,
        "reason": "Medication review — Humira",
        "status": "scheduled",
        "booked_by_agent": "scheduling",
    },
]

# ── US Demo Calls — today ─────────────────────────────────────────────────────
US_CALLS = [
    {
        "id": "call_001",
        "patient_id": "pat_maria",
        "patient_name": "Maria Santos",
        "phone_number": "+12125551234",
        "direction": "inbound",
        "intent": "scheduling",
        "duration_seconds": 187,
        "outcome": "booked",
        "agent_type": "scheduling",
        "confidence_score": 0.97,
        "cost_usd": 0.22,
        "ehr_write_back": True,
        "retell_call_id": "retell_call_001",
    },
    {
        "id": "call_002",
        "patient_id": "pat_james",
        "patient_name": "James Mitchell",
        "phone_number": "+19175555678",
        "direction": "inbound",
        "intent": "refill",
        "duration_seconds": 161,
        "outcome": "resolved",
        "agent_type": "refill",
        "confidence_score": 0.94,
        "cost_usd": 0.19,
        "ehr_write_back": True,
    },
    {
        "id": "call_003",
        "patient_id": "pat_priya",
        "patient_name": "Priya Sharma",
        "phone_number": "+16465559012",
        "direction": "inbound",
        "intent": "insurance",
        "duration_seconds": 258,
        "outcome": "resolved",
        "agent_type": "insurance",
        "confidence_score": 0.89,
        "cost_usd": 0.30,
    },
    {
        "id": "call_004",
        "patient_name": "Unknown caller",
        "phone_number": "+15551234567",
        "direction": "inbound",
        "intent": "scheduling",
        "duration_seconds": 175,
        "outcome": "booked",
        "agent_type": "scheduling",
        "confidence_score": 0.95,
        "cost_usd": 0.20,
        "ehr_write_back": True,
    },
    {
        "id": "call_005",
        "patient_id": "pat_robert",
        "patient_name": "Robert Chen",
        "phone_number": "+17185553456",
        "direction": "inbound",
        "intent": "records",
        "duration_seconds": 108,
        "outcome": "resolved",
        "agent_type": "records",
        "confidence_score": 0.96,
        "cost_usd": 0.13,
    },
]

# ── Prior auth demo data ──────────────────────────────────────────────────────
US_PRIOR_AUTHS = [
    {
        "id": "pa_001",
        "patient_id": "pat_maria",
        "patient_name": "Maria Santos",
        "medication": "Humira 40mg",
        "diagnosis_code": "M05.79",
        "insurance_carrier": "BlueCross BlueShield",
        "status": "approved",
        "submitted_at": f"{today}T08:30:00",
        "resolved_at": f"{today}T09:12:00",
        "notes": "Approved — prior auth PA-BCB-2026-001",
    },
    {
        "id": "pa_002",
        "patient_id": "pat_james",
        "patient_name": "James Mitchell",
        "medication": "Ozempic 1mg",
        "diagnosis_code": "E11.9",
        "insurance_carrier": "Aetna",
        "status": "pending",
        "submitted_at": f"{today}T07:45:00",
        "notes": "Awaiting payer response — 1 business day SLA",
    },
    {
        "id": "pa_003",
        "patient_id": "pat_priya",
        "patient_name": "Priya Sharma",
        "medication": "Dupixent 300mg",
        "diagnosis_code": "L20.9",
        "insurance_carrier": "United Healthcare",
        "status": "more_info",
        "submitted_at": f"{today}T06:00:00",
        "notes": "Additional clinical documentation required",
    },
]

# ── Analytics summary — demo ──────────────────────────────────────────────────
DEMO_ANALYTICS = {
    "today": {
        "total_calls": 23,
        "total_appointments_booked": 17,
        "total_cost_savings_usd": 221.03,
        "receptionist_hours_saved": 1.6,
        "revenue_recovered_usd": 2847.00,
        "avg_handle_time_seconds": 187,
        "patient_satisfaction_score": 4.9,
        "ai_cost_usd": 5.06,
        "autonomous_rate": 0.91,
    },
    "week": {
        "total_calls": 147,
        "total_appointments_booked": 107,
        "total_cost_savings_usd": 1412.67,
        "receptionist_hours_saved": 10.3,
        "revenue_recovered_usd": 18200.00,
        "avg_handle_time_seconds": 192,
        "patient_satisfaction_score": 4.8,
        "ai_cost_usd": 32.34,
        "autonomous_rate": 0.90,
    },
    "month": {
        "total_calls": 589,
        "total_appointments_booked": 430,
        "total_cost_savings_usd": 5660.29,
        "receptionist_hours_saved": 41.2,
        "revenue_recovered_usd": 72800.00,
        "avg_handle_time_seconds": 195,
        "patient_satisfaction_score": 4.9,
        "ai_cost_usd": 129.58,
        "autonomous_rate": 0.92,
    },
}

# ── Export all seed data ──────────────────────────────────────────────────────
SEED_DATA = {
    "clinics":      [US_CLINIC, NG_CLINIC],
    "providers":    US_PROVIDERS + NG_PROVIDERS,
    "patients":     US_PATIENTS + NG_PATIENTS,
    "appointments": US_APPOINTMENTS,
    "calls":        US_CALLS,
    "prior_auths":  US_PRIOR_AUTHS,
    "analytics":    DEMO_ANALYTICS,
}

def get_demo_clinic(region: str = "us") -> dict:
    return US_CLINIC if region == "us" else NG_CLINIC

def get_demo_analytics(period: str = "today") -> dict:
    return DEMO_ANALYTICS.get(period, DEMO_ANALYTICS["today"])
