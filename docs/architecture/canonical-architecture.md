# HEZQARA Canonical Architecture

## Status and authority

This is the canonical architecture reference for HEZQARA. When older phase notes conflict with current code or migrations, current code plus this document's verified control boundary take precedence.

E1–E8 and post-E8 forensic hardening are verified repository controls on main.

## System request and data flow

~~~text
Browser
  → Clerk session / organization
  → verified TenantContext
  → server authorization
  → FastAPI API/domain service
  → repository/integration port
  → PostgreSQL/Supabase
  → RLS/FORCE RLS
  → audit/operational evidence
~~~

The browser never establishes tenant authority. current_tenant derives organization identity from authenticated Clerk context. Database access uses transaction-scoped organization context and the authenticated database role.

## Tenant boundary

Clerk organization → verified TenantContext → transaction-local app.clerk_org_id → canonical clinics.id → PostgreSQL RLS/FORCE RLS → tenant-owned rows.

Tenant-owned relationships use composite tenant keys and tenant-bound foreign keys where required. This makes tenant membership a database invariant rather than only an application convention.

## AI architecture

~~~text
request
  → tenant authorization
  → capability/version
  → input/provenance boundary
  → policy/risk evaluation
  → provider/model
  → deterministic output validation
  → action/risk re-evaluation
  → human approval where required
  → controlled tool/side effect
  → audit/telemetry/evaluation
~~~

AI is not an authorization boundary. External patient/provider/FHIR/webhook content is untrusted data. Consequential clinical, financial, legal or safety-sensitive actions require deterministic controls and/or human escalation.

## Durable execution

PostgreSQL is authoritative for durable workflow/job/outbox state. Redis/Celery is a delivery and wake-up mechanism.

Durability controls include persistent idempotency, atomic claiming, leases, heartbeats, bounded retries, dead-letter state, recovery of expired work and explicit replay. Approval pauses preserve durable workflow state rather than relying on in-memory execution.

## Healthcare interoperability

FHIR R4 4.0.1 is the explicit resource boundary. SMART App Launch 2.2.0 supplies the OAuth authorization contract, including state/PKCE/nonce requirements where applicable.

Integration metadata is tenant scoped. Raw OAuth access/refresh tokens are intentionally excluded from the metadata persistence boundary.

Da Vinci implementation-guide versions are treated as declared capabilities. A capability declaration is not equivalent to full implementation-guide conformance or payer/EHR certification.

## Commercial and operational architecture

Subscription/provider events reconcile into PostgreSQL commercial state. E7 activation evidence, ROI snapshots and export manifests are tenant scoped.

E8 adds persisted SLO measurements, system-owned worker heartbeats, tenant-scoped operational incidents/changes/recovery evidence, authenticated readiness/snapshot APIs and release-gate evidence. Post-E8 hardening protects operational evidence from tenant mutation and enforces usage quotas at the database boundary.

## Truthfulness boundary

Configuration presence is not proof of provider connectivity. Deterministic CI providers are test-only. Production EHR/payer/payment/voice connectivity requires provider-specific configuration, credentials, endpoint validation, contracts and operational testing.

A green CI workflow proves the repository controls covered by that workflow; it does not prove live production health.

## Standards basis

The 2026 engineering reference set includes OWASP ASVS 5.0.0, NIST CSF 2.0, NIST AI RMF/AI 600-1, NIST SSDF 1.1, NIST SP 800-61r3, HL7 FHIR R4 4.0.1 and SMART App Launch 2.2.0.

## Non-claims

The repository does not claim HIPAA, GDPR, NDPA, SOC 2, ISO 27001, FHIR/SMART certification, clinical efficacy, customer ROI, production SLA attainment or arbitrary scale proof.
