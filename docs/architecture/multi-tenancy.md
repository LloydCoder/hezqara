# Multi-tenancy

Clerk Organizations are the tenant boundary. The backend verifies the session token, extracts `org_id`, checks application permissions, and creates an immutable `TenantContext`. Client-supplied clinic/tenant identifiers are never trusted as the authorization source.

For database transactions the verified organization ID is stored as a transaction-local `app.clerk_org_id`. PostgreSQL RLS policies map that organization to the clinic row. Tenant policies include SELECT, INSERT, UPDATE USING/WITH CHECK, and DELETE. FORCE RLS is used for application tables.
