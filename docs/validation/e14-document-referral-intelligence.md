# E14 — Document, Fax & Referral Intelligence

Status: IMPLEMENTED — awaiting CI/evidence gate

## Objective

Turn inbound healthcare documents into governed, traceable workflow inputs and make referral lifecycle work explicit.

## Implemented

- Fax/email/upload/EHR/API intake metadata boundary.
- Optional explicit patient matching; unmatched items remain in needs_match rather than being guessed into a patient chart.
- Classification/confidence/provenance storage.
- Deterministic document routing to patient records, authorizations, referrals, claims, tasks or review queues.
- Extraction records with field-level provenance and confidence.
- Human review state.
- Referral lifecycle transitions and event history.
- Tenant RLS, composite relational integrity and least-privilege grants.
- Automated routing-boundary tests and database proof.

## Architectural boundary

Binary storage and OCR/speech/extraction providers remain replaceable infrastructure. Hezqara owns the canonical document state, patient matching decision, routing, provenance, review and downstream workflow.

A document with ambiguous patient identity must not be silently attached to a patient.

## Exit gates

- [x] Document intake.
- [x] Patient-match boundary.
- [x] Classification/provenance.
- [x] Routing.
- [x] Extraction evidence.
- [x] Human review.
- [x] Referral lifecycle/events.
- [x] Tenant isolation.
- [x] Automated tests.
- [ ] CI/workflows fully green.
- [ ] Database/RLS/security evidence fully green.
- [ ] Main merge.
- [ ] E15 starts only after every E14 gate passes.
