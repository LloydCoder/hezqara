# E8 — Production Proving & Operating Maturity

E8 is the final product-development phase in the HEZQARA roadmap. Its purpose is to prove that the system can be operated safely, measured, recovered and scaled—not merely that application code exists.

## Operational controls

- SLO definitions have explicit targets and measurement windows.
- API availability and durable-job success are measurable from persisted evidence.
- Readiness checks cover database, durable-job schema and recent worker heartbeat.
- Incidents, changes, releases and recovery drills have durable evidence records.
- Worker liveness is represented by a heartbeat record rather than an in-memory assertion.
- Recovery evidence records measured RPO/RTO.
- Tenant-scoped operational snapshots expose only the requesting clinic's workload/incident state.
- Production claims require measured evidence; schema existence alone is not treated as proof.

## Release gate

A production release requires:
1. all required CI/security/E2E checks green;
2. database migration validation;
3. smoke validation against the deployed artifact;
4. no unresolved Sev1/Sev2 incident;
5. current backup/restore evidence;
6. measured SLO/error-budget evidence;
7. rollback path tested for the deployed version.

## Scale proving

Scale tests must measure:
- concurrent authenticated requests;
- durable-job enqueue/claim/complete throughput;
- workflow execution latency;
- database connection saturation;
- queue depth and worker recovery;
- tenant-isolation invariants under concurrency.

Synthetic data is mandatory for CI load tests. Production PHI must never be introduced into benchmark fixtures.

## Recovery proving

A restore drill is only passed when the restored environment demonstrates:
- schema/migration compatibility;
- authentication/authorization;
- tenant isolation;
- AI governance;
- durable job consistency;
- integration metadata integrity;
- measured RPO/RTO.

## Incident/change discipline

Sev1/Sev2 incidents block release until resolved or explicitly accepted by an authorized owner. Every production change has an actor, version, status and rollback evidence. Operational evidence is retained according to the applicable data-retention policy.

## Non-claims

E8 verification is an engineering validation status. It does not by itself establish regulatory certification, a production SLA, a particular cloud provider's backup configuration, or clinical efficacy.
