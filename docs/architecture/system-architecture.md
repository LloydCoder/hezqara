# HEZQARA system architecture

HEZQARA is a multi-tenant healthcare operations and AI workforce platform.

## Request flow

`Clerk session → verified Organization context → authorization → API adapter → domain service → repository/integration port → PostgreSQL/infrastructure`

The backend never treats a browser-supplied clinic identifier as an authorization primitive. Resource lookups are organization-scoped. PostgreSQL transaction-local tenant context and RLS provide defense in depth for exposed database objects.

## Domain ownership

- **Patients:** identity, demographics and lifecycle.
- **Scheduling:** availability and appointment workflows.
- **Billing:** clinic financial workflows, separate from HEZQARA SaaS subscription billing.
- **Insurance:** payer and eligibility workflows.
- **Patient engagement:** reminders, recall and communications.
- **Analytics:** derived operational measurements only; no fabricated metrics.
- **Compliance:** evidence and control workflows, not certification claims.
- **Operations:** staff and clinic workflow automation.

## AI workforce

Specialized agents share a common execution contract covering tenant/user context, permissions, idempotency, execution IDs, policy validation, provider abstraction, structured output, confidence and escalation. Model output is untrusted data. Agents cannot enforce tenant isolation themselves and do not receive direct database access.

High-impact healthcare, financial, legal and safety actions require deterministic controls and/or human escalation. The AI layer is not an authorization authority.

## Integrations and webhooks

External providers are isolated behind adapters. Webhooks are separate security boundaries with provider-specific signature verification and replay protection. Domain code does not depend directly on vendor SDK implementation details.

## Frontend

`frontend/src/app` owns route composition and `frontend/src/features` owns domain-oriented UI/API behavior. Browser requests use Clerk session tokens; the backend independently verifies authentication and authorization.

## Background work

Celery tasks are thin orchestration wrappers around domain services. Redis provides task transport and durable idempotency storage. Retries are bounded and failures escalate to explicit failure states rather than silently succeeding.

## Compliance posture

HEZQARA implements technical controls intended to support healthcare security requirements. This does **not** constitute HIPAA/GDPR certification or legal compliance. Production deployments additionally require organizational risk analysis, vendor/BAA assessment, retention and deletion controls, access reviews, incident response, backups, monitoring and documented operating procedures.
