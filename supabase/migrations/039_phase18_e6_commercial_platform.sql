-- E6: commercial platform state machine, provider events, ledger and entitlements.
ALTER TABLE public.subscriptions
  ADD COLUMN IF NOT EXISTS provider_price_id text,
  ADD COLUMN IF NOT EXISTS billing_interval text CHECK (billing_interval IS NULL OR billing_interval IN ('month','year')),
  ADD COLUMN IF NOT EXISTS version bigint NOT NULL DEFAULT 1 CHECK (version >= 1),
  ADD COLUMN IF NOT EXISTS last_provider_event_at timestamptz;

CREATE TABLE IF NOT EXISTS billing_plans (
  code text PRIMARY KEY,
  display_name text NOT NULL,
  currency text NOT NULL DEFAULT 'USD' CHECK (currency ~ '^[A-Z]{3}$'),
  monthly_amount_minor bigint NOT NULL CHECK (monthly_amount_minor >= 0),
  provider text,
  provider_price_id text,
  active boolean NOT NULL DEFAULT true,
  entitlements jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS subscription_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id text REFERENCES clinics(id) ON DELETE CASCADE,
  provider text NOT NULL,
  provider_event_id text NOT NULL,
  event_type text NOT NULL,
  status text NOT NULL DEFAULT 'received' CHECK (status IN ('received','processed','ignored','failed')),
  payload_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  error text,
  received_at timestamptz NOT NULL DEFAULT now(),
  processed_at timestamptz,
  UNIQUE(provider,provider_event_id)
);

CREATE TABLE IF NOT EXISTS commercial_ledger (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id text NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
  provider text NOT NULL,
  provider_object_id text,
  event_type text NOT NULL,
  status text NOT NULL CHECK (status IN ('pending','paid','failed','refunded','chargeback','voided')),
  amount_minor bigint,
  currency text CHECK (currency IS NULL OR currency ~ '^[A-Z]{3}$'),
  idempotency_key text NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(clinic_id,idempotency_key)
);

CREATE TABLE IF NOT EXISTS subscription_entitlements (
  clinic_id text NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
  entitlement_code text NOT NULL,
  enabled boolean NOT NULL DEFAULT true,
  limit_value bigint,
  source_plan text,
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(clinic_id,entitlement_code)
);

INSERT INTO billing_plans(code,display_name,monthly_amount_minor,entitlements)
VALUES
 ('starter','Starter',29900,'{"monthly_executions":1000,"monthly_voice_minutes":500,"monthly_messages":5000,"max_users":5,"max_locations":1}'),
 ('growth','Growth',79900,'{"monthly_executions":5000,"monthly_voice_minutes":2500,"monthly_messages":25000,"max_users":15,"max_locations":3}'),
 ('professional','Professional',149900,'{"monthly_executions":15000,"monthly_voice_minutes":7500,"monthly_messages":75000,"max_users":50,"max_locations":10}'),
 ('enterprise','Enterprise',300000,'{"monthly_executions":100000,"monthly_voice_minutes":50000,"monthly_messages":500000,"max_users":500,"max_locations":100}')
ON CONFLICT (code) DO UPDATE SET display_name=excluded.display_name,monthly_amount_minor=excluded.monthly_amount_minor,entitlements=excluded.entitlements,updated_at=now();

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['billing_plans','subscription_events','commercial_ledger','subscription_entitlements'] LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',t);
    EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY',t);
    EXECUTE format('REVOKE ALL ON public.%I FROM anon',t);
    EXECUTE format('GRANT SELECT,INSERT,UPDATE,DELETE ON public.%I TO authenticated',t);
  END LOOP;
END $$;

DROP POLICY IF EXISTS billing_plans_read ON public.billing_plans;
CREATE POLICY billing_plans_read ON public.billing_plans AS PERMISSIVE FOR SELECT TO authenticated USING (active=true);

DROP POLICY IF EXISTS subscription_events_tenant ON public.subscription_events;
CREATE POLICY subscription_events_tenant ON public.subscription_events AS RESTRICTIVE FOR ALL TO authenticated
  USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
  WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
DROP POLICY IF EXISTS subscription_events_access ON public.subscription_events;
CREATE POLICY subscription_events_access ON public.subscription_events AS PERMISSIVE FOR ALL TO authenticated
  USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
  WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

DROP POLICY IF EXISTS commercial_ledger_tenant ON public.commercial_ledger;
CREATE POLICY commercial_ledger_tenant ON public.commercial_ledger AS RESTRICTIVE FOR ALL TO authenticated
  USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
  WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
DROP POLICY IF EXISTS commercial_ledger_access ON public.commercial_ledger;
CREATE POLICY commercial_ledger_access ON public.commercial_ledger AS PERMISSIVE FOR ALL TO authenticated
  USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
  WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

DROP POLICY IF EXISTS subscription_entitlements_tenant ON public.subscription_entitlements;
CREATE POLICY subscription_entitlements_tenant ON public.subscription_entitlements AS RESTRICTIVE FOR ALL TO authenticated
  USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
  WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));
DROP POLICY IF EXISTS subscription_entitlements_access ON public.subscription_entitlements;
CREATE POLICY subscription_entitlements_access ON public.subscription_entitlements AS PERMISSIVE FOR ALL TO authenticated
  USING (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)))
  WITH CHECK (clinic_id IN (SELECT id FROM clinics WHERE clerk_org_id=current_setting('app.clerk_org_id',true)));

CREATE INDEX IF NOT EXISTS subscription_events_tenant_time ON subscription_events(clinic_id,received_at DESC);
CREATE INDEX IF NOT EXISTS commercial_ledger_tenant_time ON commercial_ledger(clinic_id,occurred_at DESC);
