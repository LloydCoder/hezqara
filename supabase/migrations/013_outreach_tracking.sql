-- Carenova Outreach Tracking — Supabase SQL
-- Track every lead from first contact to paying clinic
-- Run in Supabase SQL editor

-- Waitlist / leads table
CREATE TABLE IF NOT EXISTS waitlist (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT NOT NULL,
    region      TEXT NOT NULL DEFAULT 'us',
    source      TEXT NOT NULL DEFAULT 'landing_page',
    clinic_name TEXT,
    providers   INTEGER,
    ehr_type    TEXT,
    status      TEXT NOT NULL DEFAULT 'waitlist'
                CHECK (status IN ('waitlist','demo_booked','pilot','paying','churned','lost')),
    plan_tier   TEXT,
    mrr_usd     NUMERIC(10,2),
    notes       TEXT,
    followup_at TIMESTAMPTZ,
    converted_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
);

-- Outreach log — every email/LinkedIn/call attempt
CREATE TABLE IF NOT EXISTS outreach_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_email  TEXT NOT NULL,
    channel     TEXT NOT NULL  -- 'linkedin' | 'email' | 'whatsapp' | 'call'
                CHECK (channel IN ('linkedin','email','whatsapp','call','referral')),
    status      TEXT NOT NULL DEFAULT 'sent'
                CHECK (status IN ('sent','opened','replied','demo_booked','no_reply')),
    message_id  TEXT,
    subject     TEXT,
    notes       TEXT,
    sent_at     TIMESTAMPTZ DEFAULT now(),
    replied_at  TIMESTAMPTZ
);

-- Demo bookings
CREATE TABLE IF NOT EXISTS demo_bookings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_email  TEXT NOT NULL,
    calendly_id TEXT,
    scheduled_at TIMESTAMPTZ NOT NULL,
    duration_min INTEGER DEFAULT 15,
    status      TEXT DEFAULT 'scheduled'
                CHECK (status IN ('scheduled','completed','no_show','rescheduled')),
    notes       TEXT,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- RLS: only Lloyd can see these
ALTER TABLE waitlist        ENABLE ROW LEVEL SECURITY;
ALTER TABLE outreach_log    ENABLE ROW LEVEL SECURITY;
ALTER TABLE demo_bookings   ENABLE ROW LEVEL SECURITY;

-- Policy: service role only (no public access)
CREATE POLICY waitlist_service_only     ON waitlist        FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY outreach_service_only     ON outreach_log    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY demo_service_only         ON demo_bookings   FOR ALL USING (auth.role() = 'service_role');

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_waitlist_status      ON waitlist (status);
CREATE INDEX IF NOT EXISTS idx_waitlist_region      ON waitlist (region);
CREATE INDEX IF NOT EXISTS idx_outreach_lead        ON outreach_log (lead_email);
CREATE INDEX IF NOT EXISTS idx_outreach_channel     ON outreach_log (channel);
