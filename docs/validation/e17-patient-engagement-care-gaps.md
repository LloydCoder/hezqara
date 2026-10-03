# E17 — Patient Engagement & Care-Gap Workforce

Status: IMPLEMENTED — awaiting CI/evidence gate.

## Scope

- explicit care-gap records sourced from authorized clinic/EHR evidence
- recall/outreach proposals
- SMS/email/WhatsApp channel boundary
- patient/tenant isolation
- idempotent outreach proposals
- human approval before outbound execution
- audit evidence

## Safety boundary

E17 does not diagnose patients, independently determine clinical care gaps, triage symptoms, recommend treatment, or make autonomous clinical decisions. A care gap must enter Hezqara from an authorized source; outreach is a proposal until explicitly approved.

## Exit gates

- [x] Care-gap persistence.
- [x] Outreach proposal lifecycle.
- [x] Approval boundary.
- [x] Tenant isolation/RLS.
- [x] Idempotency.
- [ ] CI/workflows fully green.
- [ ] Main merge.
- [ ] E18 starts only after every E17 gate passes.
