# HEZQARA Canonical Architecture

## Status
Phase 9 AI reliability, evaluation and governance is implemented on the existing Phase 1–8 architecture. This document is authoritative over older phase-specific architecture summaries when they conflict with code.

## Request and data architecture

```text
Browser
  ↓
Clerk identity
  ↓
Verified organization / tenant
  ↓
Server authorization
  ↓
FastAPI API
  ↓
Domain service
  ↓
Repository
  ↓
PostgreSQL / Supabase
  ↓
RLS
  ↓
Audit
```

The browser does not establish tenant authority. `current_tenant` derives organization identity from the authenticated Clerk request; database access uses the transaction-scoped organization context and the `authenticated` role.

## AI architecture

```text
Request
  ↓
Tenant authorization
  ↓
Capability registry + immutable version
  ↓
Input contract / provenance / untrusted-content boundary
  ↓
Bounded model/provider execution
  ↓
Structured output validation
  ↓
Deterministic policy evaluation
  ↓
Risk classification
  ↓
Authorization
  ↓
Human approval where required
  ↓
Controlled workflow/tool side effect
  ↓
Audit + minimized telemetry
  ↓
Evaluation
```

AI is not an authorization boundary. External patient, provider, FHIR and webhook content is untrusted data. Clinical/high-impact decisions are not autonomously executed.

## Phase 9 governance records

Tenant-scoped governance data includes capabilities, capability versions, evaluation suites/cases/runs/results, policy decisions, execution telemetry, failure events, approvals, provider health and emergency control state. RLS and server-side permissions are required for access.

## Truthfulness

Governance metrics are derived from persisted evidence. Empty or unconfigured systems are represented as empty/configuration-required states. No production success, accuracy or connectivity is inferred from deterministic CI providers or configuration presence.

## External standards

OWASP ASVS, OWASP API Security, OWASP GenAI/LLM guidance, NIST AI RMF/GenAI Profile, NIST SSDF, HHS Security Rule guidance and HL7 FHIR/CMS interoperability guidance are engineering references, not certification claims.
