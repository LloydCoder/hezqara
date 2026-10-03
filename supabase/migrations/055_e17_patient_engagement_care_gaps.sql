-- E17: governed patient engagement and care-gap execution.
CREATE TABLE IF NOT EXISTS care_gaps (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 patient_id TEXT NOT NULL,
 gap_code TEXT NOT NULL,
 source_ref TEXT,
 description TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','in_progress','closed','dismissed')),
 evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 CONSTRAINT care_gaps_patient_tenant_fk FOREIGN KEY (clinic_id,patient_id) REFERENCES patients(clinic_id,id),
 CONSTRAINT care_gaps_clinic_id_uidx UNIQUE (clinic_id,id)
);
CREATE TABLE IF NOT EXISTS outreach_proposals (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 patient_id TEXT NOT NULL,
 care_gap_id TEXT,
 channel TEXT NOT NULL CHECK(channel IN ('sms','email','whatsapp')),
 subject TEXT,
 body TEXT NOT NULL,
 template_key TEXT,
 status TEXT NOT NULL DEFAULT 'proposed' CHECK(status IN ('proposed','approved','queued','sent','delivered','failed','cancelled')),
 reason TEXT NOT NULL,
 idempotency_key TEXT NOT NULL,
 approved_by TEXT,
 approved_at TIMESTAMPTZ,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 CONSTRAINT outreach_proposals_patient_tenant_fk FOREIGN KEY (clinic_id,patient_id) REFERENCES patients(clinic_id,id),
 CONSTRAINT outreach_proposals_gap_tenant_fk FOREIGN KEY (clinic_id,care_gap_id) REFERENCES care_gaps(clinic_id,id),
 CONSTRAINT outreach_proposals_clinic_id_uidx UNIQUE (clinic_id,id),
 CONSTRAINT outreach_proposals_idempotency_uk UNIQUE (clinic_id,idempotency_key)
);
CREATE TABLE IF NOT EXISTS outreach_events (
 id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
 clinic_id TEXT NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
 proposal_id TEXT NOT NULL,
 event_type TEXT NOT NULL,
 metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 CONSTRAINT outreach_events_proposal_tenant_fk FOREIGN KEY (clinic_id,proposal_id) REFERENCES outreach_proposals(clinic_id,id)
);
CREATE UNIQUE INDEX IF NOT EXISTS outreach_events_clinic_id_uidx ON outreach_events(clinic_id,id);

ALTER TABLE care_gaps ENABLE ROW LEVEL SECURITY; ALTER TABLE care_gaps FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS care_gaps_isolation ON care_gaps;
CREATE POLICY care_gaps_isolation ON care_gaps USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
ALTER TABLE outreach_proposals ENABLE ROW LEVEL SECURITY; ALTER TABLE outreach_proposals FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS outreach_proposals_isolation ON outreach_proposals;
CREATE POLICY outreach_proposals_isolation ON outreach_proposals USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
ALTER TABLE outreach_events ENABLE ROW LEVEL SECURITY; ALTER TABLE outreach_events FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS outreach_events_isolation ON outreach_events;
CREATE POLICY outreach_events_isolation ON outreach_events USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true))) WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
GRANT SELECT,INSERT,UPDATE,DELETE ON care_gaps,outreach_proposals,outreach_events TO authenticated;
CREATE INDEX IF NOT EXISTS idx_care_gaps_patient ON care_gaps(clinic_id,patient_id,status,updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_outreach_patient ON outreach_proposals(clinic_id,patient_id,status,created_at DESC);
