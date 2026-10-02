-- Migration 048: E10 least-privilege database grants.
-- RLS remains the authorization boundary; grants only make the tables reachable
-- to the transaction-scoped authenticated role used by request handlers.

GRANT SELECT, INSERT, UPDATE, DELETE
ON patient_access_requests, patient_intake_submissions, provider_schedules,
   schedule_slots, waitlist_entries, appointment_action_idempotency
TO authenticated;
