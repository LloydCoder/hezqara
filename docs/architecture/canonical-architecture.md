# HEZQARA Canonical Architecture

## Status

E1 AI governance, E2 canonical tenant isolation, E3 durable execution and E4 interoperability are verified engineering controls on main. This document is authoritative over older phase summaries when they conflict with current code.

## Request and data architecture

Browser → Clerk identity → verified organization/tenant → server authorization → FastAPI → domain service → repository → PostgreSQL/Supabase → RLS → audit.

The browser never establishes tenant authority. current_tenant derives organization identity from authenticated Clerk context; database access uses a transaction-scoped organization context and the authenticated database role.

## AI architecture

Request → tenant authorization → capability/version → input/provenance boundary → bounded provider/model → deterministic validation → policy/risk evaluation → authorization → human approval where required → controlled workflow/tool side effect → audit/telemetry/evaluation.

AI is not an authorization boundary. External patient, provider, FHIR and webhook content is untrusted data. Clinical/high-impact decisions are not autonomously executed.

## Tenant security

Clerk organization → verified TenantContext → transaction-local organization context → clinics.id → RLS/FORCE RLS → tenant-owned rows.

Database integrity additionally uses tenant-local composite keys and tenant-bound foreign keys where relationships span tenant-owned tables.

## Durable execution

PostgreSQL is authoritative for durable platform/workflow/outbox state. Redis/Celery is a delivery and wake-up mechanism. Leases, heartbeats, idempotency keys, retries, dead-letter state and recovery are persisted.

## Interoperability

authenticated tenant/policy → integration port → provider adapter → protocol validation → normalized result → domain state → audit/observability.

FHIR R4 4.0.1 is the explicit resource boundary. SMART App Launch 2.2.0 supplies the OAuth authorization contract and PKCE requirements. Integration metadata is tenant scoped; raw OAuth tokens are intentionally excluded from the metadata persistence boundary. Da Vinci protocol versions are recorded as capabilities, not as a claim of full implementation-guide conformance.

## Truthfulness

Configuration presence is not proof of provider connectivity. Deterministic CI providers are test-only. Production EHR/payer connectivity requires provider-specific configuration, credentials, endpoint validation, contractual prerequisites and operational testing.

## External standards

HL7 FHIR R4, SMART App Launch, Da Vinci implementation guides, OWASP API/GenAI guidance, NIST AI RMF/GenAI Profile and NIST SSDF are engineering references. They are not certification claims.
