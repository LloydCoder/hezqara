# P1 — E1–E8 Revalidation

## Scope

P1 revalidates the foundational sequence instead of accepting historical phase labels as evidence.

### E1 — Governance foundation
Verified controls inspected:
- Clerk organization context is required for authenticated requests.
- Missing Clerk configuration fails closed.
- test authentication is accepted only when `APP_ENV=test`.
- tenant permissions are enforced server-side.
- AI execution requires a tenant-scoped governance service.
- prohibited clinical/high-impact actions are denied or approval-gated.

### E2 — Tenant isolation
Verified controls inspected:
- `app.clerk_org_id` is the authoritative request tenant context.
- tenant sessions set the context transaction-locally.
- database policies resolve `clinic_id` through the authoritative Clerk organization.
- tenant-local composite keys/foreign keys provide defense in depth.

### E3 — Durable execution
Verified controls inspected:
- job/workflow leases and bounded attempts are persisted.
- expired execution leases have a deterministic recovery function.
- idempotency keys are persisted for workflow steps.
- recovery function is SECURITY DEFINER with a fixed search path and PUBLIC execute revoked.

### E4 — Interoperability metadata
Verified controls inspected:
- SMART PKCE state, nonce, redirect URI, token metadata and protocol capability state are tenant-scoped.
- token material is represented by opaque credential references rather than persisted access-token values in the inspected schema.

### E5 — Enterprise security
Verified controls inspected:
- security/privacy/recovery evidence tables are tenant-scoped and RLS-protected.
- compliance API operations are permission-gated.
- external assurance remains separate from repository evidence.

### E6 — Commercial platform
Verified controls inspected:
- billing plans, provider events, commercial ledger and entitlements have explicit tenant policies where tenant-owned.
- provider event identity and ledger idempotency are represented in database constraints.
- commercial state must not be treated as externally proven merely because the schema exists.

### E7 — First-clinic vertical slice
Verified controls inspected:
- activation state, activation evidence, ROI snapshots and export manifests are tenant-scoped.
- activation evidence is persisted rather than inferred from UI state.

### E8 — Production proving
Verified controls inspected:
- E8 workflow applies all migrations and runs dedicated production-proving SQL.
- post-E8 forensic SQL proves authenticated users cannot mutate worker heartbeats or operational evidence and cannot exceed tenant usage limits.
- recovery/SLO evidence is explicitly modeled.

## New P1 gate

`supabase/tests/p1_e1_e8_forensic.sql` adds a structural invariant:

- every public base table containing `clinic_id` must have both RLS enabled and FORCE RLS;
- `anon` must have no direct CRUD privilege on tenant-owned tables;
- the `authenticated` role must not inherit `service_role` or `postgres`;
- request-facing database access must establish transaction-local tenant context.

This complements, rather than replaces, the domain-specific E1–E8 tests.

## P1 disposition

**Engineering status:** revalidated with an additional structural security gate.

**Production status:** not inferred. Real infrastructure, credentials, provider integrations, operational drills and measured production evidence remain separate gates.

**External assurance:** not inferred. Regulatory, contractual, independent security and clinical/documentation assurance remain separate gates.
