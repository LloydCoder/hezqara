# HEZQARA Security Policy

## Scope

HEZQARA is a multi-tenant healthcare operations platform. The repository contains safeguards for authentication, authorization, tenant isolation, AI governance, interoperability, durable execution, dependency security, audit evidence and operational controls.

A green repository workflow is engineering evidence that the checked controls passed their automated gates. It is not a certification or legal-compliance determination.

## Reporting a vulnerability

**Do not disclose suspected vulnerabilities in a public issue, pull request, discussion, or documentation change.** Do not send PHI, live credentials, access tokens, private keys, or production data.

Use GitHub's private vulnerability reporting/security workflow from the repository **Security** tab. If private reporting is unavailable in the repository UI, contact the repository owner privately through GitHub and state that the message concerns a security vulnerability; do not publish exploit details while waiting for a private channel.

Include, where safe:

- affected component/path and version or commit;
- reproducible steps using synthetic data;
- security impact and attack preconditions;
- expected versus actual behavior;
- relevant logs with secrets and PHI removed;
- suggested mitigation, if known.

### Response expectations

The maintainer should acknowledge a valid private report within **3 business days**, perform initial triage within **7 business days**, and communicate a remediation/disclosure plan for confirmed vulnerabilities as soon as practical. These are project response targets, not contractual SLAs.

## Security boundary

The canonical authorization chain is:

**Clerk organization → verified TenantContext → server authorization → domain service → repository → PostgreSQL RLS/FORCE RLS**

Client-supplied clinic or tenant identifiers do not establish authority.

AI execution adds capability/version, policy/risk, approval, provider/tool authorization, execution, output validation, side-effect authorization, and audit/telemetry controls. AI output and external provider content are untrusted input.

## Implemented controls

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

## Dependency-security exception

The frontend security gate currently requires a temporary npm override for 'braces' to the reviewed upstream security-fix commit '28d440b5dd449dbf1fe6f3506cf94ecca4d02660'. The public 'braces' release line has no patched release for CVE-2026-93687 at the time of this remediation. The fix adds bounded nesting checks and regression coverage. The override must be removed once an official patched release is published and verified.

'postcss-selector-parser' is pinned to '7.1.6', the fixed release for the 2026 flat-selector CPU-exhaustion advisory. The override should be removed when all upstream consumers accept the fixed range without a root override.

Security gates must not be disabled to hide either advisory.

## Secret handling

Never commit real secrets. Examples include database credentials, Clerk secret/JWT/webhook keys, Stripe secrets/signing secrets, AI provider API keys, Retell/WhatsApp credentials and OAuth access or refresh tokens.

Public 'NEXT_PUBLIC_*' values are browser-visible and must never contain secrets.

## PHI and healthcare data

Do not use production PHI in CI, preview environments, benchmark fixtures or issue reports.

Potential ePHI incidents require an organizational and legal assessment of applicable notification, contractual and regulatory obligations. The repository does not make that legal determination.

## Incident response

Follow docs/security/incident-response.md. The runbook is aligned with NIST SP 800-61 Rev. 3 and NIST CSF 2.0.

## Security status and non-claims

HEZQARA documentation may describe controls as implemented or verified when repository evidence supports that statement.

It must not describe the project as HIPAA, GDPR, NDPA, SOC 2, ISO 27001, FHIR or SMART certified merely because repository tests are green. Production readiness additionally depends on deployment configuration, provider contracts, BAAs/DPAs where applicable, organizational safeguards, risk analysis, backups, monitoring, access reviews, incident response and independent assessment.

Security-sensitive changes should update the relevant architecture/security documentation and add or preserve adversarial tests.
