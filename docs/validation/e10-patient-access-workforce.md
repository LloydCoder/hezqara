# E10 — Patient Access Workforce

Status: IN PROGRESS
Baseline: E9 merge 2f1b6966bc55c2ef366fb76d772ad195c97570b6
Implementation branch: implementation/e10-patient-access-workforce

## Objective

Deliver a governed patient-access workforce covering intake, registration/access requests, scheduling, availability, waitlisting and pre-visit intake while preserving clinician authority and the existing authorization/RLS architecture.

## Forensic findings

Existing repository capabilities:
- Patient CRUD and tenant authorization exist.
- Appointment CRUD, availability lookup and state-transition protection exist.
- Intake and scheduling agents are registered, but their current implementations are thin wrappers without domain-specific tools.
- Existing appointments are not yet linked to a first-class Schedule/Slot availability model.
- There is no first-class patient access request queue.
- There is no structured pre-visit intake submission model.
- There is no first-class waitlist model.
- Existing provider identifiers are integration-level strings rather than a provider-directory domain.

## E10 implementation increments

### Increment A — Data foundation
Implemented on this branch:
- patient_access_requests
- patient_intake_submissions
- provider_schedules
- schedule_slots
- waitlist_entries
- nullable appointments.slot_id linkage
- tenant RLS/FORCE RLS and indexes

### Increment B — Governed API surface
Next:
- access-request lifecycle API
- structured intake submission/review API
- Schedule/Slot discovery and booking APIs
- waitlist create/match/cancel APIs
- slot-to-appointment transactional booking and replay protection
- audit events for access and scheduling side effects

### Increment C — Workforce execution
Next:
- deterministic intake/scheduling tools
- workforce policies and capability restrictions
- approval/escalation paths for consequential outbound actions
- evidence references for agent actions
- no AI authority over clinical decisions

### Increment D — Interoperability
Next:
- FHIR Schedule/Slot/Appointment mappings
- realistic payload and negative tests
- provider adapter boundary for real EHR scheduling systems
- production credential/contract prerequisites documented for E21

## External standards evidence

FHIR R4 defines Schedule as a container for time slots and Slot as bookable time on a schedule. FHIR Appointment describes the booking and documents discovery, optional availability checking, appointment request and optional waitlisting workflows. citeturn3search1turn3search0turn3search2

CMS's 2026 interoperability framework explicitly identifies modern scheduling as a use case, including real-time appointment discovery, booking, rescheduling and cancellation using FHIR Schedule, Slot and Appointment resources. This is a framework/use-case commitment, not a claim that Hezqara itself is certified or enrolled. citeturn2search2turn2search10

## Exit gates

E10 cannot close until:
- all functional API/workforce increments are implemented;
- transactional booking and concurrency are tested;
- tenant/RLS isolation is proven for all new tables;
- intake PHI boundaries and audit are tested;
- AI/tool execution remains policy governed;
- FHIR mappings and negative interoperability tests pass;
- CI, database validation, E8 regression and security workflows are green;
- documentation matches implementation;
- external provider credentials/contracts remain explicitly separated from engineering verification.
