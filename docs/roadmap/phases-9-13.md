# HEZQARA Phases 9–13

This document records the production implementation boundary for the final roadmap block.

## Phase 9 — AI Reliability, Evaluation & Governance

### E1 — AI governance enforcement

- Tenant-scoped governance is mandatory at every workforce model execution.
- Policy is evaluated before model invocation and again against the model-proposed action.
- User permission and governance tool allowlists are both enforced.
- Consequential tool/API side effects require a second governance authorization.
- Approval-required actions require a valid, unexpired human approval before the side effect can proceed.
- Secondary healthcare AI classification is governed and clinical classification remains human-reviewed.
- Adversarial tests prove the principal bypass cases fail closed.

### Verification gate

E1 is not declared closed until the complete CI workflow is green on the E1 branch/PR, including backend tests, database migrations/security tests, frontend checks, E2E, and Docker validation.

### Remaining Phase 9 work after E1

Phase 9 closure also requires the broader governance/evaluation evidence already defined by the repository: capability/version lineage, evaluation fixtures and persisted evidence, emergency controls, telemetry/failure taxonomy, and production integration proof.

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

The implementation branch is validated independently from the normal development workflow. Every migration is applied in version order; backend/security tests, tenant isolation, workflow integrity, production-like imports and frontend validation are required.

A green workflow is required before Phase 9–13 implementation work is declared closed. This document does not constitute evidence of production deployment, customer traction, compliance certification, or clinical efficacy.
