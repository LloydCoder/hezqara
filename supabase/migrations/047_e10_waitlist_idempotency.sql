-- Migration 047: E10 waitlist replay protection and lifecycle support.

ALTER TABLE waitlist_entries ADD COLUMN IF NOT EXISTS idempotency_key TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS waitlist_entries_clinic_idempotency_uidx
ON waitlist_entries(clinic_id,idempotency_key)
WHERE idempotency_key IS NOT NULL;
