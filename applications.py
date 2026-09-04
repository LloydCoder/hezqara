"""
Marketplace Application Tracker — Carenova AI

Three marketplace applications to submit this week.
Each takes 2-6 months to get approved.
Apply now — they run in parallel.

1. athenahealth Marketplace
   URL: marketplace.athenahealth.com
   Timeline: 2-3 months
   Benefit: Listed in front of 160,000+ providers

2. Epic App Orchard
   URL: fhir.epic.com/developer
   Timeline: 3-6 months
   Benefit: 20% of US ambulatory market

3. Oracle Health Marketplace (Cerner)
   URL: marketplace.oracle.com/health
   Timeline: 2-4 months
   Benefit: Your aunt's hospital + 20% of hospital market
"""

ATHENAHEALTH_APPLICATION = {
    "marketplace": "athenahealth Marketplace",
    "url": "https://marketplace.athenahealth.com",
    "developer_portal": "https://developer.athenahealth.com",
    "apply_url": "https://developer.athenahealth.com/request-access",
    "timeline": "2-3 months",
    "status": "APPLY THIS WEEK",

    "what_you_need": [
        "Company name: Tinlance Limited",
        "Product name: Carenova AI",
        "Product description: AI medical front office — scheduling, insurance, prior auth",
        "Integration type: REST API + FHIR R4",
        "Use case category: Patient Scheduling, Practice Management",
        "HIPAA BAA: will be signed upon approval",
        "SOC 2: not required for initial listing",
        "Privacy policy URL: carenova.tinlance.com/privacy",
        "Terms of service URL: carenova.tinlance.com/terms",
        "Support email: lloyd@tinlance.com",
    ],

    "listing_description": """
Carenova AI is an AI-powered medical front office platform that answers every
patient call in 600ms, books appointments directly into athenahealth, verifies
insurance eligibility in real time, and automates prior authorization submissions.

Key capabilities:
• 24/7 call answering with intelligent intent detection
• Direct appointment booking into athenahealth via REST API
• Real-time insurance eligibility verification via Availity
• Automated prior auth via FHIR Da Vinci PAS
• Prescription refill processing
• Patient recall campaigns (SMS, email, voice, WhatsApp)
• HIPAA compliant — BAA available

Designed for ambulatory practices with 1–15 providers.
Integrates with athenahealth's appointment, patient, and eligibility APIs.

Pricing: From $499/month (Starter) to $3,999/month (Enterprise).
Free 30-day trial available.
    """.strip(),

    "api_endpoints_used": [
        "GET /{practiceid}/patients — patient lookup",
        "POST /{practiceid}/patients — patient creation",
        "GET /{practiceid}/appointments/open — slot availability",
        "PUT /{practiceid}/appointments/{id} — appointment booking",
        "POST /{practiceid}/patients/{id}/insurances/{id}/eligibilitycheck",
        "POST /fhir/r4/Subscription — event webhooks",
    ],
}

EPIC_APPLICATION = {
    "marketplace": "Epic App Orchard",
    "url": "https://apporchard.epic.com",
    "developer_portal": "https://fhir.epic.com/developer",
    "apply_url": "https://appmarket.epic.com/Gallery?id=10091",
    "timeline": "3-6 months",
    "status": "APPLY THIS WEEK",

    "what_you_need": [
        "Company name: Tinlance Limited",
        "Product name: Carenova AI",
        "Epic interconnect API access required",
        "SMART on FHIR client registration",
        "Security review by Epic team",
        "Privacy policy + security documentation",
        "Demonstration environment required",
    ],

    "integration_type": "SMART on FHIR R4 — Backend Services",
    "scopes_needed": [
        "system/Patient.read",
        "system/Appointment.read",
        "system/Appointment.write",
        "system/Slot.read",
        "system/Coverage.read",
    ],
}

ORACLE_HEALTH_APPLICATION = {
    "marketplace": "Oracle Health Marketplace",
    "url": "https://marketplace.oracle.com/health",
    "apply_url": "https://www.oracle.com/health/partner-program/",
    "timeline": "2-4 months",
    "status": "APPLY THIS WEEK — your aunt's hospital is transitioning to Cerner",

    "what_you_need": [
        "Company name: Tinlance Limited",
        "Product name: Carenova AI",
        "Oracle Health partner program application",
        "FHIR R4 integration documentation",
        "HIPAA BAA with Oracle",
        "Security questionnaire",
    ],

    "why_priority": "Federal hospital transitioning to Cerner = direct warm intro opportunity",
}

MARKETPLACE_CHECKLIST = {
    "athenahealth": {
        "applied": False,
        "approved": False,
        "listed": False,
        "apply_url": "https://developer.athenahealth.com/request-access",
        "notes": "Highest priority — 160k+ providers, developer-friendly",
    },
    "epic": {
        "applied": False,
        "approved": False,
        "listed": False,
        "apply_url": "https://fhir.epic.com/developer",
        "notes": "Longest timeline — start now for 6-month window",
    },
    "oracle_health": {
        "applied": False,
        "approved": False,
        "listed": False,
        "apply_url": "https://www.oracle.com/health/partner-program/",
        "notes": "Your aunt's hospital uses Cerner — personal champion available",
    },
}

EMAIL_TEMPLATE_MEDIX = """
Subject: Carenova AI — Integration Partnership with Medix

Hi Medix Team,

I am Lloyd Nwachukwu, founder of Tinlance Limited (RC: 7962164) and Carenova AI.

Carenova is an AI-powered medical front office platform that answers patient calls,
books appointments, and verifies insurance automatically. We are currently integrating
with major EHR systems and would like to add Medix integration for the Nigerian market.

We have active contacts at Lagos clinics using Medix who would benefit from this integration.

I would like to discuss:
1. API access for appointment and patient data
2. Referral/partner program for your existing clients
3. Co-marketing opportunities in Lagos

Would you be open to a 20-minute call this week?

Best regards,
Lloyd Nwachukwu
Founder, Tinlance Limited / Carenova AI
lloyd@tinlance.com
RC: 7962164
carenova.tinlance.com
"""

MEDIX_CONTACT = {
    "company": "Medix HMS",
    "website": "https://www.medixhms.com",
    "email": "info@medixhms.com",
    "action": "Send partnership email today",
    "email_template": EMAIL_TEMPLATE_MEDIX,
}
