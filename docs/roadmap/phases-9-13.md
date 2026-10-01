# HEZQARA Phases 9–13

This document records the roadmap boundary for the Phase 9–13 implementation line.

## Phase 9 — AI Reliability, Evaluation & Governance

### E1 — AI governance enforcement — VERIFIED

- Tenant-scoped governance is mandatory at every workforce model execution.
- Policy is evaluated before model invocation and again against model-proposed actions.
- User permission and governance tool allowlists are both enforced.
- Consequential tool/API side effects require a second governance authorization.
- Approval-required actions require valid, unexpired human authorization before the side effect can proceed.
- Secondary healthcare AI classification is governed and clinical classification remains human-reviewed.
- Adversarial tests prove the principal bypass cases fail closed.
- Backend, database/RLS, frontend, security, E2E and Docker validation are green.

### Remaining Phase 9 governance maturity

The broader Phase 9 subsystem contains evaluation, emergency-control, telemetry and provider-health primitives. Further production integration and evidence work can build on E1, but E1 itself is verified and closed.

## Phase 10 — Production & Enterprise Hardening

- Database/readiness health checks.
- Tenant security posture visibility.
- Production configuration remains environment-driven.
- Security-event and health-check persistence is tenant scoped.
- No secrets are stored in source control.

## Phase 11 — Scale, Multi-Clinic & Platform Infrastructure

- Tenant plan limits for executions, communications, users, and locations.
- Daily usage accounting with idempotent upserts.
- Durable tenant-scoped platform job records with idempotency keys.
- Usage and limits are exposed through authenticated platform APIs.

## Phase 12 — Commercial / Enterprise Productization

- Starter, Growth, Professional, and Enterprise plan catalog.
- Tenant subscription state.
- Plan-to-entitlement mapping.
- Subscription change events.
- Provider identifiers are stored as references only; payment-provider behavior remains configuration dependent.

## Phase 13 — Launch, Growth & Market Expansion

- Structured onboarding checklist.
- Lead capture model and source/campaign attribution.
- Referral model.
- Growth campaign event model.
- Authenticated platform onboarding APIs.

## Verification contract

E1 has been verified by the complete green closure workflow. Future phases must retain the same rule: implementation status is not promoted to verified until their required validation gates are green. This document does not constitute evidence of production deployment, customer traction, compliance certification, or clinical efficacy.
