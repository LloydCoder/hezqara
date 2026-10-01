# E2 Canonical Tenant Security & Data Isolation

## Verified boundary

The authoritative tenant identity is the verified Clerk organization identifier. The canonical database tenant is clinics.id, resolved only through clinics.clerk_org_id.

Request flow:

Clerk organization → verified TenantContext → transaction-local app.clerk_org_id → canonical clinics.id → PostgreSQL RLS/FORCE RLS → tenant-owned rows.

## Database controls

- Every public table carrying clinic_id has RLS enabled and FORCE RLS.
- A restrictive e2_tenant_boundary policy constrains authenticated reads and writes to the resolved clinic.
- Anonymous access is revoked from tenant-owned tables.
- Tenant-owned tables receive (clinic_id,id) integrity keys.
- Cross-tenant single-column foreign-key relationships between tenant-owned tables receive tenant-bound composite foreign keys.
- Workflow relationships remain tenant-bound at the database layer.
- Client-supplied clinic IDs cannot establish tenant authority.

PostgreSQL RLS provides per-row policy enforcement, while FORCE RLS ensures the table owner is also subject to the policy.

## Adversarial proof

The E2 suite verifies:
1. Tenant A cannot read Tenant B rows.
2. Tenant A cannot insert a row owned by Tenant B.
3. Tenant A cannot reassign an existing row to Tenant B.
4. Tenant A cannot create an appointment referencing Tenant B's patient.
5. Tenant B cannot bind workflow runs, versions, steps, approvals or events to Tenant A workflow objects.
6. Every tenant-owned table remains FORCE RLS protected.

These tests implement the OWASP authorization principles of server-side enforcement, deny-by-default, least privilege and object-level authorization.

## Verification

E2 is VERIFIED after green database, backend and frontend validation on the E2 closure branch.

This is an engineering control status, not a HIPAA/NDPA/GDPR certification or production-proven claim.
