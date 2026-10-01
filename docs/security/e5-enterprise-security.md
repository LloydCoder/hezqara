# E5 Enterprise Security, Privacy & Compliance Readiness

## Status

E5 is VERIFIED as an engineering-control phase on `main`. It establishes evidence-producing controls aligned to NIST CSF 2.0, NIST SSDF/800-218A, NIST SP 800-61r3 and HIPAA Security Rule risk-analysis principles. These references are control frameworks, not certification evidence.

## Implemented evidence controls

- Tenant-scoped security incident records.
- Tenant-scoped access review records.
- Data-processing inventory with retention and agreement metadata.
- Tenant-scoped deletion-request records.
- Backup/restore drill evidence with measured RPO/RTO fields.
- RLS/FORCE RLS and authenticated-only access on new security/privacy tables.
- Dependency vulnerability scanning.
- Broad secret scanning in addition to verified-secret scanning.
- CI-generated SBOM artifact.
- Security architecture and incident-response runbooks.
- E8 adds the operational SLO, worker-liveness, incident/change and recovery evidence layer that consumes and extends the E5 foundations.

## PHI and data-flow boundary

The canonical flow is:

Clerk identity → tenant authorization → domain service → repository → PostgreSQL/RLS → external integration only when required → audit/security evidence.

PHI categories must be mapped to purpose, processor, region, retention and deletion method before production processing. AI/provider processing requires a documented business/contractual basis where applicable.

## Access review

Access reviews capture subject identity, role, permission snapshot, reviewer, decision, review time and next review. Revocation is a separate administrative action and must not be inferred from a review record alone.

## Retention and deletion

Retention is policy-driven rather than hard-coded into application behavior. Deletion requests are tracked from request through completion and must produce evidence. Legal holds, contractual requirements, backups and immutable audit records must be considered before destructive deletion.

## Incident response

Incidents move through open → contained → eradicated → recovered → closed. Evidence is preserved throughout. Response follows preparation, detection/analysis, containment, eradication/recovery and post-incident improvement.

## Supply chain

CI produces an SBOM and runs Python and npm vulnerability audits. The SBOM is an inventory, not a statement that every component is vulnerability-free.

## Key and credential lifecycle

Raw secrets remain environment/provider-managed. Production readiness requires documented ownership, least privilege, rotation cadence, expiry/revocation procedure, emergency rotation and evidence of successful rotation. The repository does not treat configuration presence as proof that a secret is current or valid.

## Recovery

E5 established restore-drill evidence and recovery controls. E8 now provides the final operating evidence layer: measured SLOs, worker liveness, operational incidents/changes and recovery-drill records.

## Non-claims

E5 does not claim HIPAA, GDPR, NDPA, SOC 2, ISO 27001, FHIR, SMART or other certification. Contractual BAAs/DPAs, organizational safeguards, legal review, provider controls and production evidence remain deployment requirements.
