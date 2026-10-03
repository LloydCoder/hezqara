# Final Forensic Audit — Post E24

This document is the final release checklist. It must be updated from actual repository evidence, not assumptions.

## Required audit surfaces

- all migrations and RLS policies
- all API routers and permissions
- all workforce/agent/tool boundaries
- all AI governance/evaluation paths
- all healthcare workflows
- FHIR/SMART and integration metadata
- secrets and PHI boundaries
- frontend routes/components and E2E coverage
- CI/security workflows
- Docker/build artifacts
- backup/restore and SLO/RTO/RPO evidence
- documentation/README consistency
- open PRs/issues and stale TODOs
- Vercel configuration and deployment gate

## Release rule

No Vercel production deployment until this audit has no unresolved blocker and all required CI/workflows are green.
