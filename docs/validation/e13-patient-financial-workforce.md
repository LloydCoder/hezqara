# E13 — Patient Financial Workforce

Status: IMPLEMENTED — awaiting CI/evidence gate

## Objective

Deliver governed patient financial operations covering statements, cost estimates, payment plans, financial assistance and payment reconciliation.

## Implemented

- Tenant-isolated patient statements.
- Explicit statement delivery channels and issued state.
- Cost estimates with service assumptions and a persistent estimate-only disclaimer.
- Responsibility arithmetic prevents estimated payer + patient responsibility from exceeding estimated charges.
- Payment plans with installment/frequency constraints.
- Financial assistance requests and reviewer decisions.
- Payment reconciliation with account/payment consistency checks and over-application prevention.
- Financial account summary combining charges, payments, reconciled payments and active plan balances.
- RLS, least-privilege grants, composite tenant foreign keys and database proof.
- Automated financial contract tests.

## Safety and financial authority

Estimates are never represented as guaranteed patient responsibility. Financial assistance decisions are explicit workflow actions. Payment reconciliation is bounded by the actual payment amount and tenant/account ownership.

## Exit gates

- [x] Statements.
- [x] Cost estimates.
- [x] Payment plans.
- [x] Financial assistance.
- [x] Payment reconciliation.
- [x] Tenant isolation and relational integrity.
- [x] Automated tests.
- [ ] CI/workflows fully green.
- [ ] Database/RLS/security evidence fully green.
- [ ] Main merge.
- [ ] E14 starts only after every E13 gate passes.
