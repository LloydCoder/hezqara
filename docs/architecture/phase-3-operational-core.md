# Phase 3 Operational Core

## Implemented

- Clerk-authenticated organization context with server-side permission checks.
- Transaction-local `app.clerk_org_id` plus `SET LOCAL ROLE authenticated` for pooled PostgreSQL connections.
- FORCE RLS for tenant-owned operational tables and explicit tenant-root policies for `clinics`.
- Patients: bounded list/search, get, create and update APIs.
- Appointments: bounded list/get/create/update APIs using UTC-aware `TIMESTAMPTZ` persistence.
- Tasks: persistent workflow records with validated state transitions.
- AI executions: persistent lifecycle records, unique tenant/agent/request idempotency, provider/model/confidence truthfulness, and governed execution boundary.
- Audit: append-oriented persistence, request correlation, metadata sanitization and database-level immutability.
- Command Center: persisted operational aggregation only; empty/zero states are authoritative.
- Frontend: typed API client plus authoritative Patients/Tasks/Appointments/Executions/Command Center data states.

## Architecture

`Browser → Clerk session → API → TenantContext → authorization → domain service → repository → PostgreSQL/RLS → audit`

AI execution follows `Agent request → authorization/policy → approved agent/tool boundary → domain service → repository → execution/audit`.

Vendor SDKs and database clients do not belong in the browser or agent layer.

## Authorization

Roles are mapped to explicit permissions server-side. UI visibility is not a security boundary. Direct API access is protected by the same permission checks.

## Tenancy

Tenant identity comes from the verified Clerk organization claim. Browser-supplied tenant identifiers are not used as authorization authority. Database access is transaction-scoped so pooled connections cannot retain tenant state.

## Audit

Audit records contain actor/resource/request/outcome metadata without secrets, authorization headers, or raw model prompts. Normal users cannot update or delete audit history.

## AI execution

Execution state is backend-authoritative. Provider, model and confidence are shown only when the runtime supplies them. A missing provider produces an explicit unavailable/escalation outcome rather than a fabricated completion.

## Testing

CI includes backend lint/type/runtime tests, frontend lint/type/build, real PostgreSQL migration execution, cross-tenant RLS tests, and an authenticated API persistence vertical slice using synthetic fixtures.

## Compliance language

These controls are engineering safeguards. They do not by themselves constitute HIPAA certification, an attestation, a BAA, or legal compliance.

## External dependencies

Telephony, messaging, clearinghouse, payer, EHR and other external providers remain unavailable/configuration-dependent unless a real integration is configured. No provider response is fabricated by Phase 3.
