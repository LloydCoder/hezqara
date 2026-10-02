# E10 — Patient Access Workforce

Status: IMPLEMENTED — awaiting final CI/evidence gate
Implementation branch: implementation/e10-patient-access-workforce-final

## Objective

Deliver a governed patient-access workforce covering access requests, structured pre-visit intake, Schedule/Slot availability, booking, rescheduling, cancellation and waitlisting while preserving tenant authorization, database isolation and human clinical authority.

## Implemented

- Tenant-isolated patient access request queue with explicit lifecycle.
- Structured pre-visit intake submission model; patient-provided responses are untrusted until reviewed.
- First-class provider schedules and bookable slots.
- Transactional slot booking with row locking and tenant-scoped idempotency.
- Appointment rescheduling and cancellation with tenant-scoped replay protection.
- Waitlist primitives with explicit priority and notification channel.
- Audit events for access and scheduling side effects.
- Composite foreign keys preventing cross-tenant patient, schedule, slot and appointment references.
- FHIR R4 Schedule, Slot and Appointment mapping boundary.
- Automated schema/state/FHIR tests.
- Database-level E10 isolation and integrity proof.

## Workforce and governance boundary

Reception, intake and scheduling agents remain subordinate to the existing authorization → AI governance → tool execution path. E10 does not grant agents clinical authority. Consequential outbound communication remains subject to existing policy/approval controls.

## Interoperability boundary

FHIR resources are generated as an internal mapping boundary only. Provider-specific endpoint credentials, SMART launch configuration, conformance testing and production contracts remain E21 work.

## Evidence

- Migration 044: E10 patient-access domain.
- Migration 045: cross-tenant composite-key integrity.
- Migration 046: booking/action idempotency.
- backend/app/domains/patient_access/fhir.py: FHIR mapping functions.
- backend/tests/test_e10_patient_access.py: schema/state/FHIR unit coverage.
- supabase/tests/e10_patient_access.sql: tenant isolation and composite-FK proof.
- CI applies all migrations in order and executes the E10 database proof.

## External standards evidence

HL7 FHIR R4 defines Schedule as an availability container, Slot as bookable time, and Appointment as the booking resource. CMS's 2026 modern-scheduling use case calls for real-time discovery, booking, rescheduling and cancellation using Schedule, Slot and Appointment through standardized FHIR APIs. Hezqara implements an internal mapping boundary here, not certification or a production EHR integration.

## Exit gates

- [x] Data foundation and tenant isolation.
- [x] Lifecycle/API surface.
- [x] Transactional booking with replay protection.
- [x] Reschedule/cancel semantics.
- [x] FHIR mapping boundary.
- [x] Audit events.
- [x] Automated tests.
- [x] Database/RLS/integrity proof.
- [ ] CI green on the implementation branch/PR.
- [ ] Security and E8 regression green.
- [ ] Final evidence snapshot and merge to main.
- [ ] E11 begins only after every E10 gate passes.
