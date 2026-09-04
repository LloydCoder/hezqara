# HEZQARA

**AI Workforce for Healthcare Operations**

HEZQARA is a multi-tenant healthcare operations platform for clinic front offices. It provides a common AI workforce runtime for reception, scheduling, intake, insurance, prior authorization, refill, records, referrals, recall and email workflows.

> **Engineering status:** architecture reconstruction and production hardening. Source-code controls do not constitute HIPAA/GDPR certification or legal compliance.

## Architecture

```text
frontend/src/app + frontend/src/features
                 │
                 ▼
        Clerk-authenticated API
                 │
                 ▼
      tenant + permission boundary
                 │
                 ▼
        HTTP adapters /api/v1
                 │
                 ▼
          domain services
          ┌──────┴──────┐
          ▼             ▼
     repositories   integration ports
          │             │
          ▼             ▼
       PostgreSQL     provider adapters
          │
          └── tenant-scoped transaction context

AI workforce follows:
request → tenant/authz → agent policy → prompt/provider → deterministic validation →
action/approved tool boundary → audit/observability → result or human escalation
```

## Backend layout

```text
backend/app/
├── core/             configuration, errors, lifecycle, logging
├── security/         Clerk auth, tenant context, permissions, audit, webhooks
├── api/              HTTP adapters and independently verified webhooks
├── domains/          patients, scheduling, billing, insurance, engagement,
│                     analytics, compliance, operations and authorization workflows
├── workforce/        common agent runtime + specialized healthcare agents
├── ai/                providers, orchestration, prompts, guardrails, evaluation, memory
├── integrations/     external-provider adapters
├── repositories/     shared persistence contracts
├── infrastructure/   database and transport infrastructure
└── tasks/             Celery application, queues and thin background jobs
```

## Multi-tenancy

The server derives the tenant from a verified Clerk Organization context. Client-supplied clinic identifiers are not trusted for authorization. Domain repositories additionally scope queries to the organization context. PostgreSQL RLS is maintained as a defense-in-depth boundary for exposed Supabase objects.

The intended security path is:

`Clerk user → organization → authenticated request → tenant context → permission → domain service → repository → tenant-scoped database transaction`

## AI workforce

All agents share lifecycle and execution contracts covering tenant identity, permissions, idempotency, execution IDs, policy checks, provider abstraction, structured output, confidence, escalation, retries and audit events. Agents do not receive direct database access. External side effects must pass through approved services/tools and deterministic authorization.

No AI agent is treated as the authority for tenant isolation, authorization, emergency clinical decisions, prescribing, or other high-risk decisions.

## Data and compliance boundary

Patient and operational data is minimized at each boundary. Secrets are environment-only. Audit records are sanitized to avoid credentials, authorization headers and unnecessary sensitive payloads. Healthcare deployments still require organizational controls including risk analysis, vendor/BAA review, retention/deletion procedures, access reviews, incident response, backups and monitoring.

## Local development

Backend: FastAPI on `:8004`  
Frontend: Next.js on `:3004`  
Redis: `:6380`

The Compose stack is for development. Production deployment must provide managed PostgreSQL/Supabase, secrets management, TLS, backups, monitoring and controlled network access.

## Validation

CI enforces repository structure, absence of generated artifacts, Python syntax/lint/tests, dependency checks, frontend lint/type-check/build and security-oriented tests. Database policy tests and full environment-backed end-to-end validation must be run against an available Supabase/PostgreSQL environment before a production release.

## License

Proprietary — Tinlance Limited. All rights reserved.
