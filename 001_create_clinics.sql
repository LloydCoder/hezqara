-- Migration 001: Clinics table
-- Multi-tenant foundation. Every other table references clinic_id.

CREATE TABLE IF NOT EXISTS clinics (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name                TEXT NOT NULL,
    clerk_org_id        TEXT UNIQUE NOT NULL,
    ehr_type            TEXT DEFAULT 'athenahealth',
    ehr_practice_id     TEXT,
    phone_number        TEXT,
    timezone            TEXT DEFAULT 'America/New_York',
    country             TEXT DEFAULT 'US',
    plan_tier           TEXT DEFAULT 'starter'
                            CHECK (plan_tier IN ('starter','pro','growth','enterprise')),
    lemonsqueezy_sub_id TEXT,
    active_agents       TEXT[] DEFAULT ARRAY['reception'],
    whatsapp_enabled    BOOLEAN DEFAULT FALSE,
    hipaa_baa_signed    BOOLEAN DEFAULT FALSE,
    hipaa_baa_date      TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: clinics can only see their own row
ALTER TABLE clinics ENABLE ROW LEVEL SECURITY;

CREATE POLICY clinics_isolation ON clinics
    USING (clerk_org_id = current_setting('app.clerk_org_id', true));

CREATE INDEX idx_clinics_clerk_org ON clinics(clerk_org_id);
