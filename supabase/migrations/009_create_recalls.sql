-- Migration 009: Patient recall campaigns
CREATE TABLE IF NOT EXISTS recall_campaigns (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    clinic_id       TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    recall_type     TEXT DEFAULT 'preventive',
    channel         TEXT DEFAULT 'sms' CHECK (channel IN ('sms','email','voice','whatsapp')),
    status          TEXT DEFAULT 'draft' CHECK (status IN ('draft','active','completed','paused')),
    total_patients  INTEGER DEFAULT 0,
    contacted       INTEGER DEFAULT 0,
    scheduled       INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE recall_campaigns ENABLE ROW LEVEL SECURITY;
CREATE POLICY recalls_isolation ON recall_campaigns
    USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id = current_setting('app.clerk_org_id', true)));
