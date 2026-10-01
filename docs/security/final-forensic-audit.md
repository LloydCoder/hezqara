# HEZQARA Final Forensic Audit — Post-E8

## Scope

This audit was performed after E1–E8 were already green on main. It covered:

- API authentication and authorization boundaries.
- Clerk organization → canonical clinic resolution.
- PostgreSQL RLS/FORCE RLS and tenant-bound relationships.
- AI governance entry points and side-effect authorization.
- Durable jobs, workflow leases, retries, idempotency and outbox state.
- FHIR R4 / SMART App Launch metadata boundaries.
- Security/privacy evidence records.
- Commercial state, provider events and quota accounting.
- First-clinic activation, evidence, ROI and export manifests.
- E8 readiness, SLO, worker liveness, incident/change/recovery evidence.
- CI workflows, database migration order, adversarial SQL, backend/frontend/E2E/Docker gates.
- README and phase documentation truthfulness.

The audit distinguishes repository controls from deployment, contractual, regulatory and clinical obligations.

## Standards basis

The audit uses current guidance from:

- OWASP API Security Top 10 — especially API1 BOLA, API4 Unrestricted Resource Consumption, API5 Function-Level Authorization, API7 SSRF and API10 Unsafe Consumption.
- OWASP agentic/AI security guidance for runtime authorization, complete mediation, least privilege and human approval.
- NIST AI RMF / GenAI Profile and secure-development guidance.
- HHS HIPAA Security Rule guidance for access control, audit controls, authentication, transmission security, risk analysis and contingency planning.
- HL7 FHIR R4 and SMART App Launch 2.2.0 for interoperability boundaries.
- Stripe API guidance for idempotent requests and verified webhook processing.

## Findings and repairs

### F-01 — E8 worker heartbeat authority

Finding: worker_heartbeats was readable and writable by the authenticated database role. A tenant user could therefore manipulate the liveness evidence used by readiness checks.

Repair: Migration 042 makes the heartbeat table system-owned, removes authenticated table privileges, adds FORCE RLS deny policies, and exposes only a read-only healthy_worker_count() SECURITY DEFINER function. Application readiness/snapshot code now consumes the protected function.

Verification: supabase/tests/post_e8_forensic.sql.

### F-02 — E8 operational evidence mutation

Finding: incident/change/recovery-drill tables granted broad authenticated write access. This weakened the evidentiary value of the operating record.

Repair: Authenticated users retain tenant-scoped SELECT access only. INSERT/UPDATE/DELETE are system-owned.

Verification: supabase/tests/post_e8_forensic.sql.

### F-03 — Commercial usage accounting bypass

Finding: platform_usage_daily could be updated through an authenticated application path without a final database-enforced quota guard.

Repair: Migration 043 adds a SECURITY DEFINER trigger guard for executions, voice minutes and messages. Unsupported metrics and quantities beyond tenant limits are rejected. The application validates metric names and returns quota violations as HTTP 409.

Verification: supabase/tests/post_e8_forensic.sql.

## Controls rechecked without additional defects requiring code changes

### Tenant isolation

The request path remains:

Clerk organization → verified TenantContext → transaction-local app.clerk_org_id → canonical clinics.id → PostgreSQL RLS/FORCE RLS.

Tenant-owned relationships use composite tenant keys where necessary. Client-supplied clinic IDs do not establish authority.

### AI governance

Workforce execution requires governance, performs pre-model policy evaluation, re-evaluates model-proposed actions, requires governed tool authorization and uses approval-backed side-effect authorization. Secondary AI classification is also governed.

### Durable execution

PostgreSQL remains authoritative for durable state. Leases, retries, idempotency and dead-letter state are persisted. Redis/Celery is treated as a delivery/wake-up mechanism rather than the source of truth.

### Interoperability

FHIR R4 and SMART App Launch 2.2.0 are explicit boundaries. OAuth metadata excludes raw access/refresh tokens. Provider-specific production connectivity remains configuration and contractual work.

### Enterprise security

Security incidents, access reviews, processing records, deletion requests and restore-drill evidence are persisted with tenant boundaries. CI includes dependency/secret scanning and SBOM generation.

### Commercial state

Provider webhook signatures are verified and provider event IDs are durably deduplicated. Subscription and ledger state are tenant scoped. Stripe idempotency is used for checkout creation.

### First-clinic lifecycle

Activation uses server-side preflight, governed workflow execution, approval, evidence, ROI and recovery state. Export manifests are explicitly manifests/counts/checksums, not a claim that raw tenant export delivery is complete.

### Production proving

E8 readiness uses database, durable-job and worker-liveness checks. SLOs, incidents, changes and recovery drills are persisted. CI proves the synthetic operating path.

## Remaining deployment prerequisites

These are intentionally not represented as repository defects:

- live Clerk configuration and organization lifecycle;
- production database/backups and tested restore procedures;
- production Redis/Celery deployment and worker monitoring;
- provider-specific EHR/payer/FHIR/SMART contracts and credentials;
- Stripe live configuration, tax/accounting/dispute operations;
- BAA/DPA and other contractual/legal controls;
- PHI inventory, retention/legal-hold policy and organizational access-review procedures;
- external penetration testing and independent compliance assessment;
- production SLO measurements and real error-budget history;
- on-call, incident-management and change-management operations.

## Verification contract

E1–E8 remain verified engineering phases. Post-E8 forensic hardening is an additional repository security gate, not a new roadmap phase.

A green workflow proves the checked repository controls. It does not by itself establish HIPAA, GDPR, NDPA, SOC 2, ISO 27001, FHIR/SMART certification, clinical efficacy, customer ROI, or an SLA.
