# Phase 6 — Healthcare Domain Engine

Phase 6 adds durable healthcare administrative primitives on top of the Phase 3–5 security and workflow spine.

## Domains

The migration `020_phase6_healthcare_domain_engine.sql` adds tenant-owned coverage, eligibility requests, billing accounts/charges/payments, claims/claim lines/adjudication, A/R work items, denials, authorizations, referrals and administrative record metadata.

Each table has a clinic relationship, RLS, FORCE RLS, authenticated grants and tenant-aware indexes. Client-supplied tenant identifiers are never used as authorization authority.

## State machines

Claims and payments use explicit server-side transitions. Invalid jumps are rejected. Financial records never imply payment receipt merely because an internal record exists.

## Provider boundary

Eligibility uses `EligibilityProvider`. CI uses a deterministic test provider; non-test deployments without a configured provider return `unavailable/provider_not_configured`. The same boundary is intended for payer, claims, payments, EHR/FHIR and document providers.

## FHIR

`backend/app/integrations/fhir/adapter.py` is an explicit interoperability boundary for FHIR-shaped resources. It validates resource type but does not claim FHIR certification or implementation-guide conformance.

## AI

`backend/app/ai/administrative.py` defines a structured administrative AI result with confidence, evidence/context, recommendation, policy decision, provider and execution ID. Administrative denial classification remains human-reviewable and does not execute side effects.

## Workforce

Phase 6 registers Revenue Cycle, Insurance Administrative and Referral/Records workforce specializations with the existing governed runtime. Existing reception/intake/insurance/prior-authorization/records/referral agents remain in the same registry.

## Security

Consequential operations remain behind Clerk organization context, permissions, domain services and tenant-scoped transactions. RLS is defense-in-depth. Approval permissions remain distinct from ordinary read/write permissions for claim submission.

## Truthful boundaries

No production payer, eligibility, clearinghouse, EHR or payment result is fabricated. Provider-dependent features are configuration-dependent and must surface unavailable/provider-error states until a real adapter is configured.

This engineering architecture does not constitute HIPAA/GDPR certification or legal compliance.
