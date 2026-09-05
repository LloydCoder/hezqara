# Phase 5 Architecture

Phase 5 turns the Phase 4 governed workflow runtime into an operational healthcare workforce layer.

## Core path

Clerk organization → verified tenant context → authorization → API → domain service → repository → PostgreSQL/RLS → audit.

Operational side effects use an outbox boundary. Communication creation persists the requested operation and dispatch event transactionally; a worker claims pending events with row locking and performs provider delivery separately.

## Operational verticals

- patient communications and preferences
- appointment availability and concurrency protection
- workflow steps for tasks, appointment updates, message classification, approvals and communication dispatch
- command-center workforce state

External providers are adapter-backed. Missing configuration is represented as unavailable rather than successful.

## AI boundary

AI receives minimized untrusted message content, produces structured output, and cannot directly authorize or mutate tenant state. Tool execution remains server-side and permission gated. Clinical decisions are outside the autonomous workforce scope.

## Interoperability

The internal appointment and communication concepts are informed by FHIR Appointment and Communication semantics without attempting to become a complete FHIR server.
