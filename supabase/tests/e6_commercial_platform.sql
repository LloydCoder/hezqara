BEGIN;
INSERT INTO clinics(id,name,clerk_org_id) VALUES
  ('e6-tenant-a','E6 Tenant A','e6_org_a'),
  ('e6-tenant-b','E6 Tenant B','e6_org_b')
ON CONFLICT DO NOTHING;

SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','e6_org_a',false);

SELECT code FROM billing_plans WHERE active=true ORDER BY code;

INSERT INTO subscription_events(clinic_id,provider,provider_event_id,event_type,payload_metadata)
VALUES ('e6-tenant-a','stripe','evt_ci_1','invoice.paid','{"provider_object_id":"in_ci_1"}');
INSERT INTO commercial_ledger(clinic_id,provider,provider_object_id,event_type,status,amount_minor,currency,idempotency_key)
VALUES ('e6-tenant-a','stripe','in_ci_1','invoice.paid','paid',29900,'USD','evt_ci_1');
INSERT INTO subscription_entitlements(clinic_id,entitlement_code,limit_value,source_plan)
VALUES ('e6-tenant-a','monthly_executions',1000,'starter');

DO $$
BEGIN
  IF (SELECT count(*) FROM subscription_events WHERE clinic_id='e6-tenant-b') <> 0 THEN
    RAISE EXCEPTION 'tenant B subscription event visible to tenant A';
  END IF;
  BEGIN
    INSERT INTO commercial_ledger(clinic_id,provider,event_type,status,idempotency_key)
    VALUES ('e6-tenant-b','stripe','cross_tenant','paid','cross_tenant');
    RAISE EXCEPTION 'cross-tenant commercial ledger write unexpectedly succeeded';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
END $$;

RESET ROLE;
ROLLBACK;
