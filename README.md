# Carenova AI

**AI Medical Front Office Platform**

Carenova replaces the human medical receptionist with 10 specialised AI agents that answer every patient call, book appointments directly in the EHR, verify insurance, process refills, and recover lost revenue — 24 hours a day, at $0.22 per call.

[![CI](https://github.com/Tinlance/carenova/actions/workflows/ci.yml/badge.svg)](https://github.com/Tinlance/carenova/actions/workflows/ci.yml)
[![HIPAA Compliant](https://img.shields.io/badge/HIPAA-Compliant-emerald)](https://github.com/Tinlance/carenova-public)
[![Tests](https://img.shields.io/badge/tests-447%20passing-emerald)](https://github.com/Tinlance/carenova/actions)

---

## The Problem

A US medical receptionist costs **$3,100/month** and handles **one call at a time**.

A clinic receiving 500 calls/month misses **20%** of them — that's 100 missed appointments, each worth ~$180 in revenue. **$18,000/month in recoverable revenue, lost.**

## The Solution

Carenova answers every call in 600ms, handles unlimited simultaneous calls, writes appointments directly back to the EHR, and costs **$499–$3,999/month**.

---

## The 10 AI Agents

| Agent | Responsibility |
|---|---|
| **Reception** | Answers every inbound call, detects intent, routes to specialist agent |
| **Scheduling** | Fetches slots, matches patient preference, books in EHR (write-back) |
| **Intake** | Collects demographics, insurance, and medical history before visit |
| **Insurance** | Real-time eligibility verification and benefits check via Availity |
| **Prior Auth** | Submits PA requests via FHIR Da Vinci PAS, polls for decisions |
| **Refill** | Parses medication requests, checks eligibility, sends to pharmacy |
| **Records** | Identity verification + HIPAA-compliant medical record release |
| **Referrals** | Creates specialist referrals, tracks status end-to-end |
| **Recall** | Proactive patient outreach campaigns — SMS, email, voice, WhatsApp |
| **Email** | Inbox triage, draft replies, appointment confirmations |

---

## Architecture

```
Patient Call (Retell AI, 600ms)
        ↓
Reception Agent (intent detection)
        ↓
Specialist Agent (Scheduling / Insurance / Refill / ...)
        ↓
EHR Write-Back (athenahealth, Epic, Helium Health)
        ↓
FusionOps Hub (all events routed through)
        ↓
Analytics + HIPAA Audit Log
```

**AI Model Routing (cost discipline):**
- Routine tasks (greeting, intent, scheduling) → Local Ollama (DeepSeek/Qwen3) — **$0**
- Clinical reasoning (prior auth, Parliament vote) → Claude Sonnet 4.6 — **pay per use**
- 80% of agent calls cost $0. Average per-call cost: $0.22 (voice only)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Python 3.12 |
| Frontend | Next.js 15 + TypeScript + Tailwind |
| Database | Supabase Frankfurt (PostgreSQL 16 + RLS) |
| Auth | Clerk (per-clinic Organisation isolation) |
| Voice (US) | Retell AI — HIPAA BAA signed, $0.07/min |
| Voice (Nigeria) | WhatsApp Business API |
| EHR (US) | athenahealth REST + FHIR R4, Epic (Phase 2) |
| EHR (Nigeria) | Helium Health |
| Billing (US) | LemonSqueezy (Starter/Pro/Growth) + Stripe (Enterprise) |
| Billing (Nigeria) | Paystack |
| AI Gateway | Policy-based routing: Ollama → Groq → Claude |
| Memory | Graphiti + FalkorDB |
| Tasks | Celery + Redis |
| Deployment | AWS EC2 Stockholm, Docker, nginx, systemd |
| CI/CD | GitHub Actions |
| Compliance | HIPAA (US) + NDPR (Nigeria) |

---

## Pricing

| Plan | Price | Providers |
|---|---|---|
| Starter | $499/month | 1–2 |
| Pro | $999/month | 3–5 |
| Growth | $1,999/month | 6–15 |
| Enterprise | $3,999/month | 15+ (Stripe, ACH, NET-30) |

**Nigeria:** ₦50,000–₦500,000/month via Paystack

---

## Markets

- **Wave 1 — US:** 230,000 independent practices. athenahealth + Epic. HIPAA.
- **Wave 2 — Nigeria:** 39,914 clinics. Zero direct competitors. WhatsApp-first. NDPR.
- **Wave 3 — UK/EU:** GDPR. NHS integration pathway.
- **Wave 4 — Philippines/SEA:** WhatsApp. Local EMRs.

---

## Quick Start (Local Development)

```bash
# Clone
git clone git@github.com:Tinlance/carenova.git
cd carenova

# Backend
cp backend/.env.example backend/.env
# Fill in: ANTHROPIC_API_KEY, RETELL_API_KEY, SUPABASE_URL,
#          CLERK_SECRET_KEY, LEMONSQUEEZY_API_KEY, STRIPE_SECRET_KEY

# Start all services
make dev

# Run tests
make test

# Health check
make health
```

---

## Deploy to EC2

```bash
# On fresh EC2 (Ubuntu 24.04)
bash infrastructure/scripts/setup_ec2.sh

# Start
sudo systemctl start carenova

# Verify
curl https://carenova.tinlance.com/health
```

---

## HIPAA Compliance

- ✅ HIPAA BAA signed with Retell AI and Supabase
- ✅ Row-Level Security on all 12 database tables
- ✅ PHI audit log on every data access
- ✅ Phone numbers masked in all logs
- ✅ AI Shield injection protection on all agent prompts
- ✅ AES-256 encryption at rest, TLS 1.3 in transit
- ✅ TruffleHog secret scanning in CI on every PR

---

## Built by

**Lloyd Nwachukwu** — Tinlance Limited (RC: 7962164)  
Forward Deployed Security Engineer | AI + Cybersecurity  
5 merged PRs to Nuclei, TruffleHog, Semgrep, Gitleaks, Slither

Co-founder/domain expert: **Obinwa Chinaza** — Medical scribe, US hospital

---

## Related

- [Public repo](https://github.com/Tinlance/carenova-public) — HIPAA docs, FHIR examples, changelog
- [FusionOps](http://13.50.16.19:8080) — Tinlance technical hub
- [KalevioAI](https://kalevio.tinlance.com) — HIPAA compliance intelligence
- [ThreatFade](https://github.com/LloydCoder/tinlance-threatfade) — Fraud detection (validated against Merlin QUIC C2, Z-score 14.76)

---

*Carenova is built on the Tinlance 20-product ecosystem. All products communicate via FusionOps. Nothing connects product-to-product directly.*
