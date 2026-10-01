# HEZQARA

**Governed AI Workforce for Healthcare Operations**

HEZQARA is a multi-tenant healthcare operations platform for clinic front offices with a governed AI workforce runtime.

## Verified phases

- **E1 — AI governance enforcement:** runtime policy, tool and side-effect governance is enforced and adversarially tested.
- **E2 — Canonical tenant security/data isolation:** Clerk organization → canonical clinic identity → server authorization → PostgreSQL RLS/FORCE RLS is enforced.
- **E3 — Durable execution/distributed reliability:** durable jobs/workflows, idempotency, leases, bounded retries, dead-lettering and recovery are persisted.
- **E4 — Healthcare interoperability:** FHIR R4 4.0.1, SMART App Launch 2.2.0/PKCE, tenant-scoped OAuth metadata and current Da Vinci capability contracts are validated.
- **E5 — Enterprise security/privacy/compliance readiness:** security incidents, access reviews, processing/retention records, deletion evidence, restore-drill evidence, broad secret scanning and SBOM generation are verified.

Engineering verification is not a HIPAA/GDPR/NDPA/SOC 2/ISO/FHIR/SMART certification, production-scale proof or clinical-efficacy claim.

## E5 control boundary

E5 establishes evidence-producing security and privacy controls aligned with NIST CSF 2.0, NIST SP 800-61r3, NIST SSDF/800-218A and HIPAA Security Rule risk-analysis principles. The repository records tenant-scoped security incidents, access reviews, processing agreements/retention metadata, deletion requests and restore drills. CI audits dependencies, scans broadly for secrets and produces an SBOM artifact.

## Canonical architecture

Browser → Clerk identity → verified tenant → server authorization → FastAPI → domain service → repository → PostgreSQL/Supabase → RLS → audit/security evidence.

AI adds capability/version → untrusted-input boundary → data/tool authorization → bounded provider/model → deterministic validation → policy/risk re-evaluation → approval/escalation → governed side effect → audit/telemetry/evaluation.

## Security boundaries

- Client-provided clinic IDs never establish tenant authority.
- PostgreSQL RLS/FORCE RLS protects tenant-owned data.
- Raw integration OAuth tokens are not persisted by the E4 metadata boundary.
- Webhooks use signature, timestamp and replay controls.
- External healthcare content is untrusted before AI processing.
- AI execution requires governance.
- Dependencies are audited; CI produces an SBOM and performs broad secret scanning.
- Security/privacy evidence tables are tenant scoped and RLS/FORCE RLS protected.

## Validation

A phase is promoted to VERIFIED only after its required GitHub Actions gates are green. E5's closure gate includes source hygiene, backend tests, database migrations/RLS/tenant integrity, integration/security tests, frontend checks, E2E, Docker, dependency scanning, broad secret scanning and SBOM generation.

## Roadmap

1. **E1 — AI governance enforcement: VERIFIED**
2. **E2 — Canonical tenant security/data isolation: VERIFIED**
3. **E3 — Durable execution/distributed reliability: VERIFIED**
4. **E4 — Production healthcare interoperability: VERIFIED**
5. **E5 — Enterprise security/privacy/compliance readiness: VERIFIED**
6. **E6 — Commercial platform completion: VERIFIED**
7. **E7 — First-clinic production vertical slice: NEXT**

8. **E8 — Production proving and scale maturity**

## Documentation

- docs/security/e5-enterprise-security.md
- docs/security/threat-model.md
- docs/security/incident-response.md
- docs/security/data-protection-and-retention.md
- docs/security/access-review.md
- docs/security/disaster-recovery.md
- docs/interoperability/e4-verification.md
- docs/compliance/engineering-controls.md

## License

Proprietary — Tinlance Limited. All rights reserved.
