# HEZQARA

**Governed AI Workforce for Healthcare Operations**

HEZQARA is a multi-tenant healthcare operations platform for clinic front offices. It provides a common AI workforce runtime for reception, scheduling, intake, insurance, prior authorization, refill, records, referrals, recall and revenue-cycle workflows.

> **Engineering status:** Phases 9–13 implementation foundation is present on the Phase 1–8 platform. Final closure remains gated by green CI, Codespace validation, adversarial security checks and production smoke testing. Source-code controls do not constitute HIPAA/GDPR, FHIR, SMART, CMS or other certification/compliance claims.

## Canonical architecture

```text
Browser
  ↓
Clerk identity
  ↓
Verified organization / tenant
  ↓
Server authorization
  ↓
FastAPI
  ↓
Domain service
  ↓
Repository
  ↓
PostgreSQL / Supabase
  ↓
RLS
  ↓
Audit
```

AI adds a governed lifecycle: capability/version → trusted/untrusted input boundary → bounded model/provider → structured output → validation → deterministic policy → risk → authorization → approval → controlled tool/workflow execution → audit/telemetry/evaluation.

AI is not an authorization boundary. External healthcare content is untrusted data. Clinical/high-impact decisions are not autonomous.

## Phase 9

The AI governance subsystem provides tenant-scoped capability/version records, evaluation suites/cases/runs/results, policy decisions, minimized execution telemetry, failure taxonomy, approval records, provider health and server-authoritative emergency controls. Governance APIs require explicit AI governance permissions and use the existing Clerk tenant/RLS architecture.

Server-side input guardrails detect common prompt-injection and cross-tenant PHI-boundary signals before model execution. These deterministic detectors are defense-in-depth, not a claim of complete prompt-injection detection.

Evaluation fixtures are synthetic-only. No production accuracy, provider connectivity or healthcare outcome is fabricated.

## Phases 10–13 foundation

The implementation branch adds enterprise readiness/security-posture primitives, tenant limits and usage accounting, platform job/subscription primitives, onboarding/referral/growth models, approval lifecycle hardening, workflow tenant referential integrity and tenant-policy hardening across the Phase 9–13 database surfaces.

These are implementation foundations; final production closure requires successful database, backend, frontend, security and runtime validation.

## Phase 7 interoperability

FHIR is an explicit R4 boundary with deterministic resource validation for common administrative resources. SMART App Launch is the authorization architecture baseline. Da Vinci HRex, PDex, CRD, DTR and PAS inform interoperability contracts. Actual production EHR, payer, clearinghouse, payment and messaging connectivity remains provider/configuration dependent.

## Phase 8 intelligence

Analytics remain deterministic and tenant scoped. Financial and insurance rates are derived from canonical source tables with explicit denominator semantics. Source tracing and governed aggregate exports preserve permission boundaries and auditability.

## Security boundaries

- PostgreSQL RLS/FORCE RLS isolates tenant-owned data.
- Client-provided clinic IDs do not establish authorization.
- Raw credentials are not stored by the integration subsystem.
- Outbound HTTP retains HTTPS, trusted-host and private-destination protections.
- Webhook signatures, timestamps and event IDs provide authentication and replay protection.
- External content is explicitly treated as untrusted before AI processing.
- AI capabilities can be disabled or forced through human approval server-side.

## Local development

Backend: FastAPI on `:8004`  
Frontend: Next.js on `:3004`  
Redis: `:6380`

## Validation

CI validates repository structure, source hygiene, Python syntax/lint/tests, integration and AI security tests, database migrations/RLS, frontend lint/type-check/build, Playwright, Docker and dependency/secret scanning. A green CI result is required before the implementation branch is merged.

## Documentation

- `docs/architecture/canonical-architecture.md`
- `docs/ai/phase-9-ai-governance.md`
- `docs/ai/phase-9-evaluation-report.md`
- `docs/phase-1-9-reconciliation.md`
- `docs/phase-8-intelligence-surface.md`
- `docs/architecture/phase-7-healthcare-interoperability.md`

## Roadmap

Phases 1–13 have implementation foundations on this branch. Remaining closure work is validation and hardening: green CI, Codespace execution of the complete validation suite, adversarial tenant/governance tests, governed tool execution, deterministic fallback verification, approval end-to-end verification, production smoke testing and final documentation reconciliation.

## License

Proprietary — Tinlance Limited. All rights reserved.
