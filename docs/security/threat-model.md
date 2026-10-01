# HEZQARA Threat Model

## Assets

- PHI and other patient data.
- Clinic/tenant identity and authorization state.
- AI policies, approvals and execution evidence.
- Integration credentials and OAuth authorization state.
- Billing/subscription data.
- Audit/security evidence.
- Source code, dependencies and deployment configuration.

## Trust boundaries

1. Browser → Clerk.
2. Clerk → backend authorization.
3. Backend → tenant database session.
4. Tenant database → PostgreSQL RLS.
5. Backend → external EHR/payer/provider.
6. External content → AI context.
7. Worker/broker → durable database state.
8. CI/dependency supply chain → deployable artifact.

## Principal threats

- BOLA/IDOR and tenant crossover.
- Forged organization/clinic context.
- Credential/token leakage.
- SSRF and malicious provider redirects.
- Webhook forgery/replay.
- Prompt injection and untrusted external content.
- AI tool/side-effect bypass.
- Duplicate or lost distributed work.
- Dependency compromise and committed secrets.
- Insider privilege abuse.
- Data retention/deletion failure.
- Backup compromise or restore failure.

## Required mitigations

- Server-side authorization and canonical tenant mapping.
- RLS/FORCE RLS plus tenant-bound foreign keys.
- Least-privilege provider credentials and opaque metadata references.
- HTTPS/host/private-destination validation.
- Signature, timestamp and event-id replay controls.
- AI governance before and after model execution.
- Durable idempotency and leases.
- Dependency audit, secret scanning and SBOM.
- Access review and incident evidence.
- Tested retention/deletion and restore procedures.

## Residual risks

Provider-specific controls, organizational identity lifecycle, human access administration, cloud configuration, legal/contractual obligations and production monitoring cannot be established solely by repository code. These remain explicit deployment controls.
