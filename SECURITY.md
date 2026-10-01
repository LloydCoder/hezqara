# HEZQARA Security Policy

## Security boundary

HEZQARA is designed as a multi-tenant healthcare operations platform. Security controls are implemented as engineering safeguards and are not a certification claim.

## Reporting

Do not disclose suspected credentials, patient information or exploit details in public issues. Report security vulnerabilities privately to the repository owner through an authorized private disclosure channel.

## Supported security controls

- Clerk authentication and organization context.
- Server-side permission checks.
- PostgreSQL RLS/FORCE RLS and tenant-bound relationships.
- Append-oriented audit/security event records.
- Webhook signature and replay protection.
- AI governance and side-effect approval.
- FHIR/SMART protocol boundary validation.
- Dependency and secret scanning.
- SBOM generation in CI.
- Incident, access-review, privacy-processing, deletion and restore-drill evidence records.

## Secret handling

Secrets are environment/configuration inputs and must not be committed. Raw OAuth access/refresh tokens are not persisted by the interoperability metadata boundary.

## Incident handling

Use the incident-response runbook in docs/security/incident-response.md. Preserve evidence, contain affected credentials/sessions, assess tenant/PHI scope, document decisions, and complete recovery and lessons-learned actions.

## Security status

A green CI workflow verifies the repository controls covered by the relevant phase. It does not establish HIPAA, GDPR, NDPA, SOC 2, ISO 27001, FHIR or SMART certification.
