# E5 Enterprise Security, Privacy & Compliance Readiness

## Status

E5 is VERIFIED as a repository engineering-control phase on main. It establishes evidence-producing controls aligned to NIST CSF 2.0, NIST SSDF 1.1, NIST SP 800-61 Rev. 3, NIST AI RMF where AI controls apply, OWASP ASVS 5.0.0 and applicable healthcare security principles.

These references are engineering frameworks and guidance, not certification evidence.

## Evidence controls

- Tenant-scoped security incident records.
- Tenant-scoped access-review records.
- Data-processing inventory with retention/agreement metadata.
- Tenant-scoped deletion-request records.
- Backup/restore drill evidence with measured RPO/RTO fields.
- RLS/FORCE RLS and authenticated-only access on security/privacy tables.
- Dependency vulnerability scanning.
- Secret scanning, including broad pattern scanning.
- CI-generated SBOM artifacts.
- Security architecture and incident-response runbooks.
- E8 operational SLO, worker-liveness, incident/change and recovery evidence.

## PHI/data-flow boundary

Clerk identity → tenant authorization → domain service → repository → PostgreSQL/RLS → external integration only when required → audit/security evidence.

Before production PHI processing, map data categories to purpose, processor, region, retention, deletion, access and contractual basis. AI/provider processing requires the applicable contractual and organizational assessment.

## Access review

Access-review evidence captures subject identity, role/permission snapshot, reviewer, decision, review time and next review. A review record does not itself revoke access; revocation is a separate administrative control.

## Retention and deletion

Retention is policy-driven. Deletion requests are tracked from intake through completion and produce evidence. Legal holds, contractual requirements, backups and immutable audit records must be considered before destructive deletion.

## Incident response

Incidents move through open → contained → eradicated → recovered → closed, with evidence preserved throughout. The current incident-response reference is NIST SP 800-61 Rev. 3.

## Supply chain

CI produces an SBOM and performs dependency/security scanning. An SBOM inventories components; it is not proof that every component is vulnerability-free.

## Credential lifecycle

Production readiness requires documented ownership, least privilege, rotation/expiry, revocation, emergency rotation and evidence of successful rotation. Configuration presence is not proof that a credential is valid or current.

## Recovery

Restore-drill evidence records measured RPO/RTO and verifies authentication, authorization, tenant isolation, durable state and relevant integration metadata after restoration.

## Non-claims

E5 does not claim HIPAA, GDPR, NDPA, SOC 2, ISO 27001, FHIR or SMART certification. BAAs/DPAs, organizational safeguards, legal review, provider controls, penetration testing and production evidence remain deployment requirements.

## References

- OWASP ASVS 5.0.0: https://owasp.org/projects/asvs
- NIST CSF 2.0: https://www.nist.gov/cyberframework
- NIST SSDF 1.1: https://csrc.nist.gov/pubs/sp/800/218/final
- NIST SP 800-61 Rev. 3: https://csrc.nist.gov/pubs/sp/800/61/r3/final
- NIST AI RMF: https://www.nist.gov/itl/ai-risk-management-framework
