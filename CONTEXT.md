# Carenova AI — Session Context
# Last updated: 2026-06-27 — ALL 6 PHASES COMPLETE

## What This Is
Carenova is an AI medical front office platform.
Replaces human medical receptionists with 10 AI agents.
Built by Lloyd (Chinaemerem Nwachukwu), Tinlance Limited RC:7962164.
Co-founder/domain expert: Obinwa Chinaza (medical scribe, US hospital).

## Build Status: COMPLETE ✅
424 backend tests passing / 0 failing
27 TypeScript frontend files
23 deployment/config files
14 Next.js dashboard pages
12 Supabase SQL migrations
3 GitHub Actions workflows
All 20 Tinlance ecosystem bridges wired

## Stack (Locked)
Backend:    FastAPI + Python 3.12 — EC2 Stockholm port 8004
Frontend:   Next.js 15 + TypeScript + Tailwind — port 3004
Database:   Supabase Frankfurt (PostgreSQL 16 + pgvector + RLS)
Auth:       Clerk (Organisations per clinic — multi-tenant)
Billing US: LemonSqueezy store 247127 (Starter/Pro/Growth)
Billing US Enterprise: Stripe (ACH + NET-30)
Billing NG: Paystack
Voice US:   Retell AI ($0.07/min, HIPAA BAA)
Voice NG:   WhatsApp Business API (works on 2G)
EHR US:     athenahealth (Phase 1) + Epic FHIR (Phase 2)
EHR NG:     Helium Health
LLM:        Claude Sonnet 4.6 (complex) → Ollama local (routine, free)
Memory:     Graphiti + FalkorDB (persistent per clinic)
Comms:      Resend (email) + Twilio (SMS)
Storage:    Cloudflare R2 (audio + documents)
Tasks:      Celery + Redis (recall, PA polling, reminders, analytics)
CI/CD:      GitHub Actions → EC2 Stockholm port 8004
Compliance: HIPAA (US) + NDPR (Nigeria)

## EC2 Port Map
8000 — ThreatFade
8002 — AI Shield
8003 — ResilientAI
8004 — Carenova ← This product
8080 — FusionOps (hub)

## All 10 Agents — Built and Tested
Reception, Scheduling, Intake, Insurance, Prior Auth,
Refill, Records, Referrals, Recall, Email Agent

## Markets
Wave 1 — US:      $499–$3,999/month, athenahealth, Retell AI voice
Wave 2 — Nigeria: ₦50K–₦500K/month, Helium Health, WhatsApp-first
Wave 3 — UK/EU:   Phase 3 roadmap
Wave 4 — SEA/PH:  Phase 4 roadmap

## Ecosystem Rule
Nothing connects product-to-product directly.
Everything routes through FusionOps (hub) at 13.50.16.19:8080.
AI Shield is the only exception — surveillance infrastructure.

## To Deploy
1. git clone git@github.com:Tinlance/carenova.git /home/ubuntu/carenova
2. cp backend/.env.example backend/.env && fill in all values
3. bash infrastructure/scripts/setup_ec2.sh
4. sudo certbot --nginx -d carenova.tinlance.com
5. sudo systemctl start carenova
6. curl https://carenova.tinlance.com/health → {"status": "ok"}
