# HEZQARA

**Governed AI Workforce for Healthcare Operations**

HEZQARA is a multi-tenant healthcare operations platform for clinic front offices. It provides a governed AI workforce runtime for reception, scheduling, intake, insurance, prior authorization, refill, records, referrals, recall and patient-engagement workflows.

> **Engineering status:** E1 AI governance, E2 canonical tenant isolation, E3 durable execution and E4 interoperability controls are VERIFIED on the current mainline after full repository validation. E5–E8 remain roadmap work. Engineering verification is not a HIPAA/GDPR/FHIR/SMART/CMS certification, production-scale proof, clinical-efficacy claim or customer-outcome claim.

## Canonical architecture

Browser → Clerk identity → verified tenant → server authorization → FastAPI → domain service → repository → PostgreSQL/Supabase → RLS → audit.

AI adds: capability/version → untrusted-input boundary → data/tool authorization → bounded provider/model → deterministic validation → action/risk re-evaluation → approval/escalation → governed side effect → audit/telemetry/evaluation.

The LLM is never an authorization source. External healthcare content is untrusted data. Clinical/high-impact decisions are not autonomous.

## Verified phases

### E1 — AI governance enforcement
- Workforce execution fails closed without tenant-scoped governance.
- Policy is enforced before provider invocation and against model-proposed actions.
- Tools require user permission and governance allowlisting.
- Consequential side effects require approval-backed governance authorization.
- Secondary AI paths are governed.
- Adversarial bypass tests are green.

### E2 — Canonical tenant security/data isolation
- Clerk organization → canonical clinic ID is the tenant authority chain.
- Tenant-owned tables use RLS/FORCE RLS.
- Client-supplied clinic IDs cannot establish authority.
- Cross-tenant workflow and foreign-key integrity is enforced at the database layer.
- Adversarial tenant-isolation tests are green.

### E3 — Durable execution/distributed reliability
- PostgreSQL is authoritative for durable job/workflow state.
- Broker delivery is a wake-up mechanism, not completion authority.
- Idempotency, leases, heartbeats, bounded retries, dead-lettering and crash recovery are persisted.
- Workflow execution survives approval pauses and worker loss.
- Adversarial duplicate/lease/recovery tests are green.

### E4 — Production healthcare interoperability
- FHIR R4 (4.0.1) is the explicit resource boundary.
- SMART App Launch 2.2.0 is the OAuth/PKCE contract.
- OAuth state, PKCE, redirect and OIDC nonce requirements are validated.
- Raw access/refresh tokens are not returned or persisted by the integration metadata boundary.
- Current Da Vinci contracts are recorded for HRex 1.2.0, CRD 2.2.1, DTR 2.2.0, PAS 2.2.1 and PDex 2.2.0.
- Integration metadata is tenant isolated.
- Deterministic FHIR/SMART interoperability tests are green.

E4 is an interoperability engineering boundary; actual EHR/payer production connectivity still requires provider-specific credentials, contracts, endpoint allowlists, sandbox validation and operational certification where applicable.

## Security boundaries

- PostgreSQL RLS/FORCE RLS isolates tenant-owned data.
- Client-provided clinic IDs do not establish authorization.
- Raw integration credentials/tokens are not persisted by the integration metadata layer.
- Outbound HTTP retains HTTPS, trusted-host and private-destination protections.
- Webhooks require signatures, timestamps and replay protection.
- External content is untrusted before AI processing.
- AI execution requires governance.
- Supabase Data API exposure is separate from RLS and must be explicitly granted where required.

## Validation

The repository's required validation covers structure/source hygiene, backend tests, database migrations/RLS/tenant integrity, FHIR/interoperability checks, AI governance/security, frontend lint/type/build, Playwright E2E, Docker and dependency/secret scanning. A phase is not promoted to VERIFIED until its required workflow gates are green.

## Roadmap

1. **E1 — AI governance enforcement: VERIFIED**
2. **E2 — Canonical tenant security/data isolation: VERIFIED**
3. **E3 — Durable execution/distributed reliability: VERIFIED**
4. **E4 — Production healthcare interoperability: VERIFIED**
5. **E5 — Enterprise security, privacy and compliance readiness: NEXT**
6. **E6 — Commercial platform completion**
7. **E7 — First-clinic production vertical slice**
8. **E8 — Production proving and scale maturity**

The roadmap deliberately separates engineering verification from production proving.

## License

Proprietary — Tinlance Limited. All rights reserved.
