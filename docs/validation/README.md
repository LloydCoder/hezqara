# HEZQARA Validation Evidence

This directory contains repository-verifiable evidence and explicit gaps. It is not a regulatory certification record.

## Evidence hierarchy

- **Repository evidence:** source, migrations, tests, CI/security results, build artifacts and documented control definitions.
- **Production evidence:** deployed runtime checks, real provider connectivity, measured SLO/RPO/RTO, backup/restore and operational drills.
- **External assurance:** independent penetration testing, privacy/legal artifacts, BAAs/DPAs, clinical/documentation evaluation, interoperability conformance, contracts and customer evidence.

Do not collapse these categories.

## Canonical evidence

- [P0 forensic reconciliation](p0-forensic-reconciliation.md)
- [E9–E24 roadmap](../roadmap/enterprise-e9-e24.md)
- [E8 production proving](../operations/e8-production-proving.md)
- [Vercel deployment topology](../operations/vercel-deployment.md)

## CI interpretation

A green workflow proves only the assertions encoded by that workflow. It does not prove that external providers, production secrets, cloud infrastructure, legal agreements, regulatory obligations, or customer operations are complete.

Production PHI must never be introduced into CI, previews, benchmarks, local fixtures, or forensic validation.
