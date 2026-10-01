# HEZQARA

**Governed AI Workforce for Healthcare Operations**

HEZQARA is a multi-tenant healthcare operations platform for clinic front offices. Its architecture combines governed AI execution, tenant-isolated healthcare operations, healthcare interoperability, durable workflows, commercial controls and evidence-backed operating maturity.

## Verified engineering phases

1. E1 — AI governance enforcement — VERIFIED
2. E2 — Canonical tenant security/data isolation — VERIFIED
3. E3 — Durable execution/distributed reliability — VERIFIED
4. E4 — Production healthcare interoperability — VERIFIED
5. E5 — Enterprise security/privacy/compliance readiness — VERIFIED
6. E6 — Commercial platform completion — VERIFIED
7. E7 — First-clinic production vertical slice — VERIFIED
8. E8 — Production proving/operating maturity — VERIFIED

“Verified” means the documented engineering acceptance gates are implemented and green. It does not mean HIPAA/SOC 2 certification, clinical validation, arbitrary production-scale proof, or a specific cloud-provider configuration.

## Canonical control chain

Tenant identity → authorization → domain service → repository → PostgreSQL/RLS.

AI: tenant identity → authorization → capability/version → policy/risk → approval → provider/tool authorization → execution → output validation → side-effect authorization → audit/telemetry.

Operations: authenticated readiness → worker liveness → SLO/error budget → incident/change control → backup/restore evidence → rollback/release gate → measured production smoke.

## E8 — Final roadmap phase

E8 provides durable operational evidence for SLOs, worker heartbeats, incidents, changes and recovery drills, authenticated operational readiness, tenant-scoped operational snapshots and deterministic CI proving. The final repository gate also validates database/RLS, backend, frontend, E2E, security, dependency/secret scanning and Docker builds. A post-E8 forensic gate additionally verifies platform-owned operational evidence and database-enforced usage quotas.

## Final verification boundary

All eight engineering phases are now verified on `main`. This is not a claim that HEZQARA is certified, legally compliant, clinically validated, or proven against arbitrary production scale. Deployment-specific controls, provider contracts, BAAs/DPAs, organizational safeguards, live integrations, monitoring, backups and operating evidence remain required for an actual production launch.

## Documentation

- `docs/architecture/canonical-architecture.md`
- `docs/architecture/system-architecture.md`
- `docs/architecture/multi-tenancy.md`
- `docs/ai/phase-9-e1-enforcement.md`
- `docs/security/phase-10-e2-tenant-isolation.md`
- `docs/reliability/phase-11-e3-durable-execution.md`
- `docs/interoperability/e4-verification.md`
- `docs/security/e5-enterprise-security.md`
- `docs/commercial/e6-verification.md`
- `docs/operations/e7-first-clinic-vertical-slice.md`
- `docs/operations/e8-production-proving.md`
- `docs/security/final-forensic-audit.md`
- `docs/operations/vercel-deployment.md`

## License

Proprietary — Tinlance Limited. All rights reserved.
