# E12 — Revenue Cycle Workforce

Status: IMPLEMENTED — awaiting CI/evidence gate

## Objective

Deliver a governed revenue-cycle workforce from claim creation through scrubbing, submission, payer status, adjudication, A/R, denials and appeals.

## Implemented

- Idempotent claim creation with claim lines.
- Claim-line reconciliation during deterministic scrubbing.
- Explicit scrub results with ruleset version and machine-readable issues.
- Ready/submission gates require a passing scrub.
- Consequential claim submission requires the existing approval permission.
- Submission attempts are tenant-scoped and replay-safe.
- Claim status event history.
- Adjudication recording with payment/patient-responsibility reconciliation.
- A/R work-item creation and lifecycle updates.
- Denial queue and denial creation.
- Appeal drafting with evidence/provenance.
- Appeal submission requires approval permission.
- Tenant RLS, least-privilege grants and database proof.
- Automated lifecycle/aging tests.

## Interoperability boundary

Hezqara's internal claim model is designed around the HIPAA-adopted U.S. electronic transaction ecosystem. CMS identifies ASC X12N 837 version 5010 as the adopted health-care claim transaction standard and X12 835 version 5010 for electronic remittance advice. The current phase deliberately stops at a governed adapter boundary; actual payer/clearinghouse connectivity, companion-guide conformance, enrollment, credentials and production transaction certification remain E21 work. CMS also describes front-end edits, acknowledgments, rejection and denial processing as distinct stages in electronic claims submission.

## Safety and authority

AI can scrub, classify, prioritize, draft and route revenue-cycle work. It cannot silently submit consequential claims or appeals; those actions remain approval-gated.

## Exit gates

- [x] Claim creation and line model.
- [x] Deterministic claim scrubbing.
- [x] Scrub-before-ready/submission enforcement.
- [x] Approval-gated submission.
- [x] Submission replay protection.
- [x] Adjudication and reconciliation.
- [x] A/R queue.
- [x] Denial queue.
- [x] Appeal evidence/drafting.
- [x] Approval-gated appeal submission.
- [x] Tenant isolation/RLS.
- [x] Automated tests.
- [ ] CI/workflows fully green.
- [ ] Database/RLS/security evidence fully green.
- [ ] Main merge.
- [ ] E13 starts only after every E12 gate passes.
