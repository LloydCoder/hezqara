# HEZQARA

**Governed AI Workforce for Healthcare Operations**

HEZQARA is a multi-tenant healthcare operations platform for clinic front offices. It provides a common AI workforce runtime for reception, scheduling, intake, insurance, prior authorization, refill, records, referrals, recall and patient-engagement workflows.

> **Engineering status:** Phase 9 E1 — AI governance enforcement is VERIFIED on the E1 closure branch after backend, database/RLS, frontend, security, E2E and Docker validation. Phases 10–13 remain implementation foundations and are not represented as production-proven. Source-code controls do not constitute HIPAA/GDPR, FHIR, SMART, CMS or other certification/compliance claims.

## Canonical architecture

Browser → Clerk identity → verified tenant → server authorization → FastAPI → domain service → repository → PostgreSQL/Supabase → RLS → audit.

AI adds a governed lifecycle: capability/version → untrusted-input boundary → data/tool authorization → bounded provider/model → deterministic output validation → action/risk re-evaluation → approval/escalation → governed side-effect authorization → audit/telemetry/evaluation.

The LLM is never an authorization source. External healthcare content is untrusted data. Clinical/high-impact decisions are not autonomous.

## Phase 9 — E1 verified

E1 establishes runtime governance as a mandatory execution boundary.

- Workforce model execution fails closed without tenant-scoped governance.
- Policy is enforced before model invocation and again against model-proposed actions.
- Tool calls require both authenticated user permission and governance allowlisting.
- Consequential tool/API side effects pass through a separate governance authorization barrier.
- Approval-required side effects require approved, unexpired authorization bound to the execution, policy and action.
- Secondary healthcare message classification is governed through the same tenant policy boundary.
- Clinical message classification retains human review.
- Adversarial tests cover missing governance, policy denial, approval gates, governed tool denial and the secondary AI path.
- Governance state, policy decisions, approvals, telemetry and failures remain tenant scoped.

E1 verification is an engineering validation result, not a production-readiness or regulatory-certification claim.

## Phases 10–13 foundation

The branch contains implementation foundations for enterprise hardening, scale/platform infrastructure, commercial primitives and launch/growth models. These remain separate roadmap work and should not be interpreted as production-proven functionality.

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
- Workforce AI execution cannot proceed without a governance service.

## Validation

The closure workflow validates repository structure, source hygiene, Python syntax/lint/tests, integration and AI security tests, database migrations/RLS, frontend lint/type-check/build, Playwright E2E, Docker and dependency/secret scanning. A green closure workflow is required before E1 is considered verified.

## Documentation

- docs/architecture/canonical-architecture.md
- docs/architecture/ai-architecture.md
- docs/ai/phase-9-ai-governance.md
- docs/ai/phase-9-e1-enforcement.md
- docs/ai/phase-9-evaluation-report.md
- docs/phase-1-9-reconciliation.md
- docs/security/phase-9-ai-security-controls.md

## Roadmap

1. **E1 — AI governance enforcement: VERIFIED**
2. **E2 — Canonical tenant security/data isolation: NEXT**
3. **E3 — Durable execution and distributed reliability**
4. **E4 — Production healthcare interoperability**
5. **E5 — Enterprise security, privacy and compliance readiness**
6. **E6 — Commercial platform completion**
7. **E7 — First-clinic production vertical slice**
8. **E8 — Production proving and scale maturity**

A green E1 workflow verifies the engineering controls covered by E1; it does not prove production scale, regulatory certification, customer outcomes or clinical efficacy.

## License

Proprietary — Tinlance Limited. All rights reserved.
