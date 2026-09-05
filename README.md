# HEZQARA

**AI Workforce for Healthcare Operations**

HEZQARA is a multi-tenant healthcare operations platform for clinic front offices. It provides a common AI workforce runtime for reception, scheduling, intake, insurance, prior authorization, refill, records, referrals, recall and revenue-cycle workflows.

> **Engineering status:** Phase 7 healthcare interoperability layer implemented on the Phase 6 administrative domain engine. Source-code controls do not constitute HIPAA/GDPR, FHIR, SMART or other certification/compliance claims.

## Architecture

```text
frontend
   ↓
Clerk-authenticated API
   ↓
tenant + permission + policy
   ↓
domain services
   ↓
integration ports
   ↓
provider adapters
   ↓
external healthcare system
   ↓
validated / normalized result
   ↓
domain state → workflow → audit / analytics
```

AI never receives arbitrary external URLs, credentials, OAuth scopes or provider authority. External healthcare content is treated as untrusted data.

## Phase 7 interoperability

The integration subsystem provides provider contracts, capability metadata, health state, tenant-scoped integration records, credential metadata references, external-reference mappings, integration request state, webhook lifecycle state, synchronization records, failure records and rate-limit state.

FHIR is an explicit R4 boundary with deterministic resource validation for common administrative resources. SMART App Launch is the authorization architecture baseline. Da Vinci HRex, PDex, CRD, DTR and PAS inform the interoperability contracts. Actual production EHR, payer, clearinghouse, payment and messaging connectivity remains provider/configuration dependent.

Deterministic CI providers are isolated and named `test-*`; they are not production integrations.

## Security boundaries

- PostgreSQL RLS/FORCE RLS isolates every Phase 7 tenant-owned table.
- Client-provided clinic IDs do not establish authorization.
- Raw credentials are never stored by the integration subsystem; only opaque credential metadata references are persisted.
- Outbound HTTP requires HTTPS and an explicit trusted host allowlist and rejects private/loopback/link-local destinations and redirects.
- Webhook signatures, timestamps and event IDs provide authentication and replay protection.
- Integration errors are normalized and retry classification is bounded.
- External content is explicitly labeled as untrusted before AI processing.

## Truthful provider states

`not_configured`, `configuration_required`, `healthy`, `degraded`, `unavailable`, `authentication_failed`, `rate_limited` and `provider_error` are distinct. A configured credential is not evidence of connectivity or health.

## Local development

Backend: FastAPI on `:8004`  
Frontend: Next.js on `:3004`  
Redis: `:6380`

## Validation

CI validates repository structure, source hygiene, Python syntax/lint/tests, dedicated integration and AI security tests, database migrations/RLS, frontend lint/type-check/build, genuine Playwright browser tests, Docker and dependency/secret scanning.

## Documentation

- `docs/architecture/phase-6-healthcare-domain-engine.md`
- `docs/architecture/phase-7-healthcare-interoperability.md`

## License

Proprietary — Tinlance Limited. All rights reserved.
