# HEZQARA

**AI Workforce for Healthcare**

Hezqara is a healthcare operations automation platform for clinic front offices. It coordinates AI agents for reception, scheduling, intake, insurance workflows, prior authorization, refills, records, referrals, recall, and email while keeping external side effects behind authorization, tenant controls, audit logging, and human-review boundaries.

> **Engineering status:** canonical architecture consolidation and production hardening. This repository is not a regulatory certification.

## Canonical repository layout

```text
hezqara/
├── backend/
│   ├── app/
│   │   ├── agents/        # AI workforce implementations
│   │   ├── integrations/  # EHR, messaging, voice and external systems
│   │   ├── llm/           # model routing and evaluation
│   │   ├── models/        # persistence/domain models
│   │   ├── routers/       # HTTP API boundary
│   │   ├── security/      # authentication, authorization, audit/compliance
│   │   ├── services/      # application services and data access
│   │   ├── tasks/         # Celery workers/schedules
│   │   ├── utils/         # pure shared utilities
│   │   └── main.py
│   ├── tests/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── requirements*.txt
├── frontend/
│   ├── src/app/           # Next.js App Router
│   ├── src/components/
│   ├── src/hooks/
│   ├── src/lib/
│   ├── src/types/
│   ├── src/proxy.ts       # Clerk/Next request boundary
│   ├── Dockerfile
│   └── package.json
├── supabase/migrations/   # ordered database migrations
├── docs/                  # architecture and operating documentation
├── ops/                   # operational scripts
├── docker-compose.yml
└── .github/workflows/
```

## Product boundary

Hezqara automates administrative and front-office work. Clinical diagnosis, prescribing, emergency triage, and other high-risk clinical decisions are outside the default product boundary and require separate clinical, regulatory, and human-oversight controls.

## Core workforce

| Agent | Responsibility |
|---|---|
| Reception | Inbound patient communication, intent detection, routing |
| Scheduling | Availability, booking, rescheduling and EHR write-back |
| Intake | Demographics, insurance and pre-visit collection |
| Insurance | Eligibility and benefits workflow support |
| Prior Authorization | Preparation, submission and status tracking |
| Refill | Medication-request intake and authorized routing |
| Records | Identity verification and record-release workflows |
| Referrals | Specialist referral creation and tracking |
| Recall | Proactive patient outreach campaigns |
| Email | Inbox triage, drafting and appointment communications |

## Technology

- **API:** FastAPI / Python 3.12
- **Web:** Next.js / React / TypeScript
- **Data:** PostgreSQL / Supabase
- **Auth:** Clerk
- **Voice:** Retell adapter
- **Messaging:** WhatsApp adapter
- **Tasks:** Celery / Redis
- **Memory:** Graphiti / FalkorDB adapter
- **Deployment:** Docker / AWS
- **CI:** GitHub Actions

## Security boundary

Authentication and tenant context are enforced through Clerk at the API boundary; client API requests obtain and forward the active Clerk session token. Sensitive audit metadata is sanitized before structured logging. Secrets are environment-driven and production credentials have no code-level fallback.

Healthcare workloads still require operational controls beyond source code: risk analysis, least privilege, vendor/BAA review, retention and deletion policy, access reviews, incident response, backups, monitoring, and appropriate regulatory/legal assessment.

## Engineering gates

A release is not considered production-ready until clean-checkout backend startup, tests, database migrations, frontend type-check/build, Docker builds, tenant-isolation tests, secret scanning, AI safety/tool-authorization evaluations, and critical end-to-end workflows all pass.

## License

Proprietary — Tinlance Limited. All rights reserved.
