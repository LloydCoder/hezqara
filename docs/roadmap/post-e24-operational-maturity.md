# HEZQARA Post-E24 Operational Maturity Roadmap — E25–E32

**Status:** Proposed serial extension following the canonical E1–E24 engineering sequence  
**Release principle:** Repository CI, production evidence, and external assurance are separate evidence classes.

This document extends rather than rewrites the frozen [E9–E24 engineering roadmap](enterprise-e9-e24.md). A later phase must not be marked complete while its prerequisites or earlier phase gates remain unresolved. Any change that invalidates a prior control reopens that phase's evidence gate.

## Phase sequence

| Phase | Scope | Required exit evidence |
|---|---|---|
| E25 | Production Readiness and Dependency Health Contract | Liveness and readiness are distinct; API readiness checks database, durable-job schema, and worker heartbeat; frontend readiness probes API readiness; failure paths return safe 503 responses; automated tests pass; real production configuration and authenticated smoke checks are verified. |
| E26 | Live Clinic Pilot and Operational Validation | Approved pilot scope and agreements; synthetic/test data separated from authorized pilot data; baseline and post-deployment operational metrics; documented exception, escalation, override, and rollback exercises; signed acceptance and remediation ledger. |
| E27 | Independent Security and Privacy Assurance | Independent penetration test; threat-model refresh; tenant-escape and agent/tool-abuse tests; findings remediated or formally risk-accepted; applicable privacy/data-protection assessment and evidence retention. Formal certification is claimed only after the relevant independent process. |
| E28 | Capacity, Resilience and Disaster-Recovery Qualification | Representative concurrent-tenant and workflow load tests; measured saturation and queue recovery; tested backups/restores; measured RPO/RTO; failover and rollback evidence; SLO results against a stated measurement window. |
| E29 | Continuous AI Evaluation and Model Lifecycle Governance | Versioned workforce-specific evaluation datasets; quality, safety, abstention, escalation and human-override measures; prompt-injection/tool-misuse tests; model/provider/prompt change controls; enforced release thresholds and rollback evidence. |
| E30 | Enterprise Customer Operations | Named service and incident owners; onboarding/offboarding procedures; support escalation and communication; customer-specific access reviews; rehearsed incident, continuity, and change-management processes. |
| E31 | Commercial Validation and Unit Economics | Evidence from actual customers; verified billing and entitlement lifecycle; measured onboarding/support cost, gross margin, acquisition cost and retention; customer outcomes and ROI methodology; forecasts clearly separated from realized results. |
| E32 | Continuous Assurance and Enterprise Maturity | Recurring control testing, access recertification, dependency and model reviews, DR exercises, audit evidence, incident learning, risk ownership, and release gates operate as a durable business process. |

## E25 — Production Readiness and Dependency Health Contract

### Engineering contract

- `GET /health` is a process-liveness endpoint only.
- `GET /ready` returns HTTP 200 only when database connectivity, durable-job schema access, and a recent healthy worker heartbeat all pass; otherwise it returns HTTP 503.
- `GET /api/health` returns HTTP 200 only when the frontend authentication configuration exists and its server-side API origin passes `/ready`; missing configuration, unreachable API, or degraded dependencies return HTTP 503.
- The `/api/v1/ready` rewrite exposes the same minimal status contract for monitoring. Readiness output must not include secrets, connection strings, provider payloads, or patient data.
- Exceptions must fail closed without returning raw exception text.
- CI must test healthy readiness, degraded worker state, and unavailable database behavior.

### External production gate

The engineering implementation alone does not close E25. The owner must supply valid environment configuration through the deployment secret/configuration manager, deploy a reachable API and worker stack with the required database and Redis connectivity, and run authenticated smoke tests against the actual deployment. Never invent, commit, or expose production credentials.

Minimum frontend configuration is documented in [Vercel deployment topology](../operations/vercel-deployment.md). Backend configuration is documented in `backend/.env.example`. Use distinct development, preview/staging, and production credentials and databases.

### E25 completion checklist

- [ ] API liveness remains independent of dependency readiness.
- [ ] API readiness verifies database, durable-job schema, and worker heartbeat.
- [ ] Readiness fails closed for each dependency failure and for missing database configuration.
- [ ] Frontend readiness probes the API readiness endpoint rather than process liveness.
- [ ] Automated backend, frontend, database/RLS, E2E, Docker, security, E8 proving, P0 reconciliation, and phase-validation workflows are green on the exact candidate revision.
- [ ] Real production environment values are present in deployment configuration and have been reviewed without exposing their values.
- [ ] Authenticated production smoke tests prove organization/tenant mapping, tenant isolation, worker health, and safe health/readiness responses.
- [ ] Production deployment, rollback, backup/restore, and monitoring evidence are recorded.

E25 remains **blocked** until every applicable item is evidenced. Do not start E26 implementation as a substitute for an unresolved E25 release gate.

## Shared exit-gate rules for E26–E32

1. Define the scope, owner, risks, acceptance criteria, and required evidence before implementation.
2. Use synthetic data in CI, preview, and benchmarks. Use real healthcare data only under the applicable authorization, contract, privacy controls, and approved environment.
3. Run the relevant tests on the exact candidate revision; do not infer passing checks from another branch or commit.
4. Audit the completed phase's implementation, failure modes, security boundaries, database effects, documentation, and workflow evidence before advancing.
5. Record unresolved external dependencies explicitly. A repository workflow cannot establish that a legal agreement was signed, a provider credential works, a clinic accepted the system, or a certification was awarded.
6. After E32, run a final repository-wide forensic audit across source, migrations, tests, workflows, configuration templates, documentation, dependency inventories, deployment evidence, and all open GitHub work.

## External reference frameworks

Use the versions and obligations applicable at the time and in the jurisdiction of deployment; references are control-design aids, not certification claims:

- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [HHS HIPAA Security Rule risk-analysis guidance](https://www.hhs.gov/hipaa/for-professionals/security/guidance/guidance-risk-analysis/index.html)
- [HL7 FHIR R4](https://hl7.org/fhir/R4/)
