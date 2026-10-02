# E11 — Insurance & Authorization Workforce

Status: IMPLEMENTED — awaiting CI/evidence gate

## Objective

Deliver a governed insurance and authorization workforce covering coverage, eligibility, benefits, prior-authorization lifecycle, documentation requirements, payer-adapter boundaries and FHIR interoperability mappings.

## Implemented

- Tenant-scoped coverage/eligibility foundation retained from the healthcare domain engine.
- Idempotent eligibility verification API with explicit provider abstraction.
- Benefit records for network status, copay, coinsurance, deductible and out-of-pocket values.
- Prior-authorization lifecycle with explicit state transitions.
- Submission is approval-gated; agents cannot bypass the existing governance/approval layer.
- Authorization documentation requirements and evidence/provenance records.
- Authorization status/event history.
- Payer adapter registry without storing raw credentials in the application database.
- FHIR R4 mapping boundary for Coverage, CoverageEligibilityRequest, CoverageEligibilityResponse and authorization Task.
- Tenant RLS and least-privilege authenticated grants.
- Automated governance/FHIR tests.

## Safety and authority

E11 does not autonomously approve clinical care, determine diagnosis or recommend treatment. AI may collect, validate, route and draft administrative authorization work, while consequential submission remains governed and approval-controlled.

## Interoperability boundary

The current phase implements an internal FHIR R4 mapping boundary and adapter contract. Production payer credentials, SMART/OAuth configuration, payer-specific conformance testing and full Da Vinci CRD/DTR/PAS production transactions remain E21 work.

Current HL7 U.S. Realm publications list Da Vinci CRD 2.2.1, DTR 2.2.0 and PAS 2.2.1 on FHIR R4. CMS's prior-authorization final rule requires impacted payers to implement Prior Authorization APIs beginning generally in 2027 and recommends CRD/DTR/PAS for interoperability. citeturn3search0turn2search3

## Exit gates

- [x] Coverage/eligibility/benefits data model.
- [x] Eligibility provider abstraction and idempotency.
- [x] Authorization state machine.
- [x] Approval-gated submission.
- [x] Documentation requirement/evidence model.
- [x] Authorization event history.
- [x] Payer adapter registry.
- [x] FHIR mapping boundary.
- [x] Tenant isolation/grants.
- [x] Automated tests.
- [ ] CI/workflows fully green.
- [ ] Database/RLS/security evidence fully green.
- [ ] Main merge.
- [ ] E12 starts only after every E11 gate passes.
