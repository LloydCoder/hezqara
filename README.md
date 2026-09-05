# HEZQARA

**AI Workforce for Healthcare Operations**

HEZQARA is a multi-tenant healthcare operations platform for clinic front offices. It provides a common AI workforce runtime for reception, scheduling, intake, insurance, prior authorization, refill, records, referrals, recall and revenue-cycle workflows.

> **Engineering status:** Phase 6 healthcare domain engine implemented on the Phase 5 foundation. Source-code controls do not constitute HIPAA/GDPR certification or legal compliance.

## Architecture

```text
frontend
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
   ├── patients / scheduling / engagement
   ├── insurance / eligibility / authorization
   ├── billing / claims / A/R / denials
   └── referrals / records / operations / analytics
   │
   ├── repositories → PostgreSQL/RLS
   └── integration ports → provider adapters

AI workforce:
request → tenant/authz → policy → provider → deterministic validation →
approved tool/action → audit/observability → result or human escalation
```

## Phase 6 domain engine

Phase 6 adds durable administrative primitives for coverage and eligibility, billing accounts/charges/payments, claims and adjudication foundations, A/R work queues, denial management, prior authorization, referrals and record metadata. State transitions are explicit and validated server-side.

The interoperability boundary is `backend/app/integrations/fhir/adapter.py`. It validates FHIR-shaped resources without claiming certification or implementation-guide conformance. External payer/eligibility/clearinghouse/EHR/payment connectivity remains provider/configuration dependent.

## Multi-tenancy

The server derives the tenant from a verified Clerk Organization context. Client-supplied clinic identifiers are not trusted for authorization. Domain repositories and SQL writes scope records to the organization context. PostgreSQL RLS with FORCE RLS is defense-in-depth for tenant-owned Phase 6 objects.

The intended security path is:

`Clerk user → organization → authenticated request → tenant context → permission → domain service → repository → tenant-scoped database transaction`

## AI workforce

All agents share lifecycle and execution contracts covering tenant identity, permissions, idempotency, execution IDs, policy checks, provider abstraction, structured output, confidence, escalation, retries and audit events. Phase 6 registers Revenue Cycle, Insurance Administrative and Referral/Records specializations using the existing governed runtime.

AI is not the authority for tenant isolation, authorization, clinical decisions or external side effects. Administrative recommendations remain subject to policy and human review where consequential.

## Data and compliance boundary

Patient and operational data is minimized at each boundary. Secrets are environment-only. Audit records avoid credentials, authorization headers and unnecessary sensitive payloads. Healthcare deployments still require organizational controls including risk analysis, vendor/BAA review, retention/deletion procedures, access reviews, incident response, backups and monitoring.

## Local development

Backend: FastAPI on `:8004`  
Frontend: Next.js on `:3004`  
Redis: `:6380`

## Validation

CI enforces repository structure, source hygiene, Python syntax/lint/tests, database/RLS tests, frontend lint/type-check/build, browser E2E, Docker validation and security-oriented checks. Production provider connectivity must be configured and independently validated before a live healthcare deployment.

## Documentation

See `docs/architecture/phase-6-healthcare-domain-engine.md` for the Phase 6 domain, interoperability, AI and security boundaries.

## License

Proprietary — Tinlance Limited. All rights reserved.
