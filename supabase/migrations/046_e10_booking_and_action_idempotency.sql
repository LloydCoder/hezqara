-- Migration 046: E10 booking/action replay protection.

ALTER TABLE appointments ADD COLUMN IF NOT EXISTS booking_idempotency_key TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS appointments_clinic_booking_idempotency_uidx
ON appointments(clinic_id,booking_idempotency_key)
WHERE booking_idempotency_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS appointment_action_idempotency (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    appointment_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('cancel','reschedule')),
    idempotency_key TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (clinic_id,idempotency_key),
    CONSTRAINT appointment_action_idempotency_appointment_tenant_fk
      FOREIGN KEY (clinic_id,appointment_id) REFERENCES appointments(clinic_id,id)
);

ALTER TABLE appointment_action_idempotency ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointment_action_idempotency FORCE ROW LEVEL SECURITY;

CREATE POLICY appointment_action_idempotency_isolation
ON appointment_action_idempotency
USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

CREATE INDEX IF NOT EXISTS idx_appointment_action_idempotency_appointment
ON appointment_action_idempotency(clinic_id,appointment_id,action);
