# Compliance Engineering Controls

HEZQARA uses engineering controls intended to support security, privacy and contractual obligations.

## Control families

- Identity and access management: Clerk authentication, organization authorization, server-side permission checks and access-review evidence.
- Tenant isolation: PostgreSQL RLS/FORCE RLS, canonical clinic mapping and tenant-bound relationships.
- Audit/security evidence: sanitized audit logging plus security incident records.
- Privacy: processing inventory, purpose/region/retention/deletion metadata and deletion-request evidence.
- Resilience: durable execution, backups/restore-drill evidence and recovery procedures.
- Supply chain: dependency vulnerability audits, broad secret scanning and SBOM generation.
- AI security: mandatory governance, approval-backed side effects and untrusted-content boundaries.
- Interoperability: FHIR/SMART protocol validation and tenant-scoped integration metadata.

HHS identifies risk analysis as foundational to the HIPAA Security Rule safeguard program. NIST CSF 2.0 provides the Govern, Identify, Protect, Detect, Respond and Recover lifecycle, and NIST SP 800-61r3 provides current incident-response guidance. citeturn2search48turn2search49turn2search16

These are engineering controls, not legal advice or certification. HIPAA/GDPR/NDPA, BAAs/DPAs, security assessments, organizational policies, physical safeguards, provider contracts and production evidence remain deployment responsibilities.
