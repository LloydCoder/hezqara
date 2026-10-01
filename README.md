# HEZQARA

**Governed AI Workforce for Healthcare Operations**

HEZQARA is a multi-tenant healthcare operations platform for clinic front offices. Its architecture combines governed AI execution, tenant-isolated healthcare operations, interoperability, durable workflows, commercial controls and evidence-backed operating maturity.

## Verified engineering phases

1. E1 — AI governance enforcement — VERIFIED
2. E2 — Canonical tenant security/data isolation — VERIFIED
3. E3 — Durable execution/distributed reliability — VERIFIED
4. E4 — Production healthcare interoperability — VERIFIED
5. E5 — Enterprise security/privacy/compliance readiness — VERIFIED
6. E6 — Commercial platform completion — VERIFIED
7. E7 — First-clinic production vertical slice — VERIFIED
8. E8 — Production proving/operating maturity — IN PROGRESS

“Verified” means the documented engineering acceptance gates are implemented and green. It does not mean HIPAA/SOC 2 certification, clinical validation, arbitrary production-scale proof, or a specific cloud-provider configuration.

## Canonical control chain

Tenant identity → authorization → domain service → repository → PostgreSQL/RLS.

AI: tenant identity → authorization → capability/version → policy/risk → approval → provider/tool authorization → execution → output validation → side-effect authorization → audit/telemetry.

Operations: authenticated readiness → worker liveness → SLO/error budget → incident/change control → backup/restore evidence → rollback/release gate → measured production smoke.

## E8

E8 adds durable operational evidence for SLOs, worker heartbeats, incidents, changes and recovery drills, plus authenticated operational readiness and tenant-scoped operational snapshots. Its final gate additionally requires database/RLS, backend, frontend, E2E, security, dependency and Docker validation.

## Documentation

See `docs/operations/e8-production-proving.md`, `docs/operations/e7-first-clinic-vertical-slice.md`, `docs/security/disaster-recovery.md`, `docs/security/incident-response.md`, `docs/security/threat-model.md`, and `docs/architecture/canonical-architecture.md`.
