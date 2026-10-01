# HEZQARA Security Policy

## Scope

HEZQARA is a multi-tenant healthcare operations platform. Its repository contains technical safeguards for authentication, authorization, tenant isolation, AI governance, interoperability, durable execution, security evidence and operational controls.

A green CI workflow is evidence that the checked repository controls passed their automated gates. It is not a certification or legal-compliance determination.

## Security boundary

The canonical authorization chain is:

**Clerk organization → verified TenantContext → server authorization → domain service → repository → PostgreSQL RLS/FORCE RLS**

Client-supplied clinic or tenant identifiers do not establish authority.

AI execution adds policy, capability, tool, approval, output-validation and side-effect controls. AI output and external healthcare/provider content are treated as untrusted input.

## Implemented security controls

- Clerk authentication and organization context.
- Server-side authorization and permission checks.
- PostgreSQL RLS/FORCE RLS and tenant-bound relational integrity.
- Append-oriented audit/security evidence.
- Provider webhook signature verification and replay protection.
- AI governance, tool allowlists, approval gates and side-effect authorization.
- FHIR R4 / SMART protocol boundary validation.
- Dependency and secret scanning.
- CI-generated SBOM.
- Incident, access-review, privacy-processing, deletion and restore-drill evidence.
- Operational evidence protections and database-enforced usage quotas.

## Reporting a vulnerability

Do not disclose suspected credentials, patient information, access tokens, exploit chains or other sensitive details in a public GitHub issue.

Use an authorized private disclosure channel available to the repository owner. Include enough information to reproduce and assess the issue without sending real PHI or live credentials.

When reporting, prefer:

- affected component/path;
- reproducible steps using synthetic data;
- security impact;
- expected versus actual behavior;
- relevant logs with secrets and PHI removed;
- suggested mitigation, if known.

## Secret handling

Never commit real secrets. Examples include database credentials, Clerk secret/JWT/webhook keys, Stripe secrets/signing secrets, AI provider API keys, Retell/WhatsApp credentials and OAuth access or refresh tokens.

Public NEXT_PUBLIC_* values are intentionally browser-visible and must never contain secrets.

## PHI and healthcare data

Do not use production PHI in CI, preview environments, benchmark fixtures or issue reports.

Potential ePHI incidents require an organizational and legal assessment of applicable notification, contractual and regulatory obligations. The repository does not make that legal determination.

## Incident response

Follow docs/security/incident-response.md. The runbook is aligned with NIST SP 800-61 Rev. 3 and NIST CSF 2.0.

## Security status and non-claims

HEZQARA documentation may describe controls as implemented or verified when repository evidence supports that statement.

It must not describe the project as HIPAA, GDPR, NDPA, SOC 2, ISO 27001, FHIR or SMART certified merely because repository tests are green. Production readiness additionally depends on deployment configuration, provider contracts, BAAs/DPAs where applicable, organizational safeguards, risk analysis, backups, monitoring, access reviews, incident response and independent assessment.

Security-sensitive changes should update the relevant architecture/security documentation and add or preserve adversarial tests. Security gates must not be disabled merely to unblock a build.
