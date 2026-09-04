"""
FadeReach Email Sequences — Carenova onboarding and follow-up emails.
These are the actual email bodies that fire when a clinic joins the waitlist
or completes onboarding steps.

Sequences:
  clinic_onboarding_us — for US clinic signups
  clinic_onboarding_ng — for Nigeria clinic signups
  demo_followup        — after a demo is completed
  trial_activation     — when clinic completes onboarding
  first_call_milestone — when clinic handles first real call
  week_1_summary       — weekly savings summary
"""

# ── US Onboarding Sequence ────────────────────────────────────────────────────

US_SEQUENCE = {
    "id": "clinic_onboarding_us",
    "name": "US Clinic Onboarding",
    "triggers": ["waitlist_signup", "demo_booking"],
    "emails": [
        {
            "step": 1,
            "delay_hours": 0,
            "subject": "Your Carenova demo is confirmed",
            "preview_text": "We'll show you live — with your real phone number",
            "body": """Hi {{first_name}},

Thanks for signing up for Carenova. I'm Lloyd, the founder.

Here's exactly what we'll do in our 15-minute demo:

1. Connect your athenahealth (or whatever EHR you use) to Carenova
2. Call your clinic's number — live, in real time
3. Show you the appointment booked directly in your EHR

No slides. No pre-recorded video. Just your system, live.

To make the demo useful, can you tell me:
— What EHR do you use?
— What's your biggest front desk headache right now?

Just reply to this email. I read every response personally.

Talk soon,
Lloyd
Founder, Carenova / Tinlance Limited

P.S. If you want to skip straight to the demo: carenova.tinlance.com/demo
""",
        },
        {
            "step": 2,
            "delay_hours": 72,
            "subject": "Quick question about your front desk",
            "preview_text": "Most clinics are losing $18,000/month without knowing it",
            "body": """Hi {{first_name}},

A quick question: do you know how many patient calls your clinic misses every month?

Most practices receiving 500 calls/month miss about 20% — that's 100 appointments.
At $180 average, that's $18,000 in revenue walked out the door. Every month.

Carenova answers every call in 600ms, books directly in your EHR, and costs $999/month.

The ROI calculator shows your specific numbers: carenova.tinlance.com/roi-calculator

Or reply and tell me how many calls you get per day — I'll run the numbers for you personally.

Lloyd
""",
        },
        {
            "step": 3,
            "delay_hours": 168,
            "subject": "Case study: 23 appointments booked in one day",
            "preview_text": "Zero extra staff. Zero missed calls. $999/month.",
            "body": """Hi {{first_name}},

One of our early clinics — a 3-provider family medicine practice — had a specific problem:
they were missing calls during lunch and after 5pm every single day.

In the first week with Carenova:
— 23 appointments booked (including 9 after hours)
— 0 calls missed
— $387 in daily savings vs their previous receptionist cost

The doctor told us: "I didn't realize how much we were losing until it stopped."

If you want to see how this would work at your practice, I can have a demo ready in 24 hours.

Just reply with your EHR and I'll set it up.

Lloyd
""",
        },
        {
            "step": 4,
            "delay_hours": 336,
            "subject": "Last email — is this still interesting?",
            "preview_text": "No pressure either way",
            "body": """Hi {{first_name}},

I've sent a few emails about Carenova and I don't want to be that annoying follow-up sequence.

If the timing isn't right — totally fine. Feel free to bookmark this and come back when it is:
carenova.tinlance.com

If you're still interested but have a specific question or concern, just reply. I'll answer within the hour.

Lloyd

P.S. If you know another clinic owner who might benefit from this, I'd appreciate the introduction.
""",
        },
    ],
}

# ── Nigeria Onboarding Sequence ───────────────────────────────────────────────

NG_SEQUENCE = {
    "id": "clinic_onboarding_ng",
    "name": "Nigeria Clinic Onboarding",
    "triggers": ["waitlist_signup_ng", "whatsapp_signup"],
    "emails": [
        {
            "step": 1,
            "delay_hours": 0,
            "subject": "Carenova — your hospital's AI front desk",
            "preview_text": "Works on WhatsApp. Works on 2G. Built for Nigerian clinics.",
            "body": """Hello {{first_name}},

Thank you for your interest in Carenova.

I am Lloyd, the founder. I built Carenova specifically for Nigerian hospitals and clinics — including hospitals that are still using pen and paper.

Here is what Carenova does for your hospital:

— Patients book appointments via WhatsApp (number they already have)
— Patient records stored securely — no lost files
— Nurses create records by sending a WhatsApp message
— Works on 2G internet — no expensive hardware needed
— NDPR compliant — Nigerian data protection

We can set your hospital up for FREE for 30 days. No contract. No upfront cost.

Can we schedule a 10-minute call or WhatsApp demo this week?

Lloyd Nwachukwu
Founder, Tinlance Limited (RC: 7962164)
+234 — WhatsApp welcome
""",
        },
        {
            "step": 2,
            "delay_hours": 48,
            "subject": "For hospitals still using pen and paper",
            "preview_text": "Carenova was built for you specifically",
            "body": """Hello {{first_name}},

Many Nigerian hospitals tell me the same thing: "We know we need to go digital, but the software is too complicated or too expensive."

Carenova solves both problems:

Simple: Your nurses send WhatsApp messages. That is all.
"New patient: Amaka Obi, female, 15 March 1990, 08031234567"
Carenova creates the patient record automatically.

Affordable: ₦25,000/month — less than one nurse's monthly transport allowance.

No special hardware. No IT department. No training beyond 30 minutes.

The 30-day free trial means zero risk to try it.

Lloyd
""",
        },
    ],
}

# ── Demo Follow-up ────────────────────────────────────────────────────────────

DEMO_FOLLOWUP = {
    "id": "demo_followup",
    "name": "Post-Demo Follow-up",
    "triggers": ["demo_completed"],
    "emails": [
        {
            "step": 1,
            "delay_hours": 1,
            "subject": "Your Carenova demo — next steps",
            "preview_text": "Everything we discussed + how to get started",
            "body": """Hi {{first_name}},

Great talking with you today.

To recap what we covered:

✓ Live call answered in 600ms
✓ Appointment booked directly into {{ehr_type}}
✓ Insurance verified in the background
✓ Cost: {{plan_price}}/month vs {{receptionist_cost}}/month for a receptionist

To start your free 30-day pilot:
1. Sign up: {{checkout_url}}
2. I'll personally configure your EHR connection within 2 hours
3. Your first call goes live same day

Any questions, reply here or WhatsApp me directly.

Lloyd
""",
        },
        {
            "step": 2,
            "delay_hours": 48,
            "subject": "Did you get a chance to look at the pilot offer?",
            "preview_text": "30 days free. No contract.",
            "body": """Hi {{first_name}},

Just following up on our demo.

The 30-day free pilot offer is still open — I want you to see real results before you pay anything.

Start here: {{checkout_url}}

Or if you have a specific question — pricing, HIPAA compliance, EHR compatibility, anything — just reply. I'll answer within the hour.

Lloyd
""",
        },
    ],
}

# ── Trial Activation ──────────────────────────────────────────────────────────

TRIAL_ACTIVATION = {
    "id": "trial_activation",
    "name": "Trial Activation",
    "triggers": ["subscription_created"],
    "emails": [
        {
            "step": 1,
            "delay_hours": 0,
            "subject": "Welcome to Carenova — let's get you live",
            "preview_text": "Your AI receptionist is ready to configure",
            "body": """Hi {{first_name}},

Welcome to Carenova. Your {{plan_tier}} plan is active.

Here's what happens next:

Step 1 (5 min): Complete your clinic setup
→ carenova.tinlance.com/dashboard/onboarding

Step 2 (10 min): Connect your EHR ({{ehr_type}})
I'll walk you through this personally if you want:
→ Reply with a time that works and I'll jump on a call

Step 3: Make your first test call
Call your number and watch the dashboard light up.

Step 4: Go live
Flip the switch and never miss a patient call again.

Most clinics are fully live within 2 hours of signing up.

I'm here for every step.

Lloyd
lloyd@tinlance.com
""",
        },
    ],
}

# ── Week 1 Summary ────────────────────────────────────────────────────────────

WEEK_1_SUMMARY = {
    "id": "week_1_summary",
    "name": "Week 1 Summary",
    "triggers": ["7_days_after_activation"],
    "emails": [
        {
            "step": 1,
            "delay_hours": 0,
            "subject": "Your first week with Carenova — the numbers",
            "preview_text": "{{total_calls}} calls handled. {{savings}} saved.",
            "body": """Hi {{first_name}},

Your first week with Carenova:

📞 {{total_calls}} calls answered by AI
📅 {{appointments_booked}} appointments booked
💰 ${{savings_usd}} saved vs receptionist cost
⏱ {{hours_saved}} hours of staff time freed
⭐ {{satisfaction_score}}/5 patient satisfaction

Your most active agent: {{top_agent}} ({{top_agent_calls}} calls)

At this rate, Carenova will save {{clinic_name}} ${{monthly_savings}} this month.

The full breakdown is in your dashboard:
→ carenova.tinlance.com/dashboard/analytics

Anything you want me to adjust or optimize? Just reply.

Lloyd
""",
        },
    ],
}

# ── All sequences ─────────────────────────────────────────────────────────────

ALL_SEQUENCES = {
    "clinic_onboarding_us": US_SEQUENCE,
    "clinic_onboarding_ng": NG_SEQUENCE,
    "demo_followup":        DEMO_FOLLOWUP,
    "trial_activation":     TRIAL_ACTIVATION,
    "week_1_summary":       WEEK_1_SUMMARY,
}

def get_sequence(sequence_id: str) -> dict:
    return ALL_SEQUENCES.get(sequence_id, {})

def get_all_sequences() -> dict:
    return ALL_SEQUENCES
