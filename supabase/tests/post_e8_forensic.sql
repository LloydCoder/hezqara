-- Final forensic hardening tests for post-E8 operational and quota boundaries.
BEGIN;

INSERT INTO clinics(id,name,clerk_org_id) VALUES
  ('forensic-clinic-a','Forensic Clinic A','forensic-org-a'),
  ('forensic-clinic-b','Forensic Clinic B','forensic-org-b')
ON CONFLICT (id) DO NOTHING;

INSERT INTO tenant_limits(clinic_id,plan_code,monthly_executions,monthly_voice_minutes,monthly_messages)
VALUES ('forensic-clinic-a','starter',1,2,3)
ON CONFLICT (clinic_id) DO UPDATE SET monthly_executions=1,monthly_voice_minutes=2,monthly_messages=3;

INSERT INTO operational_incidents(clinic_id,severity,status,category,summary)
VALUES ('forensic-clinic-a','high','open','test','tenant incident');
INSERT INTO operational_incidents(clinic_id,severity,status,category,summary)
VALUES (NULL,'high','open','platform','global platform incident');

SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','forensic-org-a',false);

INSERT INTO platform_usage_daily(clinic_id,usage_date,metric,quantity)
VALUES ('forensic-clinic-a',current_date,'executions',1)
ON CONFLICT (clinic_id,usage_date,metric) DO UPDATE SET quantity=excluded.quantity;

DO $$
BEGIN
  BEGIN
    UPDATE platform_usage_daily
    SET quantity=2
    WHERE clinic_id='forensic-clinic-a' AND usage_date=current_date AND metric='executions';
    RAISE EXCEPTION 'usage quota bypass succeeded';
  EXCEPTION WHEN check_violation THEN NULL;
  END;
END $$;

DO $$
BEGIN
  BEGIN
    INSERT INTO platform_usage_daily(clinic_id,usage_date,metric,quantity)
    VALUES ('forensic-clinic-a',current_date,'unsupported_metric',1);
    RAISE EXCEPTION 'unsupported usage metric accepted';
  EXCEPTION WHEN check_violation THEN NULL;
  END;
END $$;

DO $$
BEGIN
  BEGIN
    INSERT INTO platform_usage_daily(clinic_id,usage_date,metric,quantity)
    VALUES ('forensic-clinic-b',current_date,'executions',1);
    RAISE EXCEPTION 'cross-tenant usage write accepted';
  EXCEPTION WHEN insufficient_privilege OR check_violation THEN NULL;
  END;
END $$;

DO $$
BEGIN
  BEGIN
    INSERT INTO worker_heartbeats(worker_id,queue)
    VALUES ('forensic-user-write','test');
    RAISE EXCEPTION 'authenticated worker heartbeat write accepted';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
END $$;

DO $$
DECLARE n bigint;
BEGIN
  SELECT public.healthy_worker_count(interval '2 minutes') INTO n;
  IF n < 0 THEN RAISE EXCEPTION 'invalid worker count'; END IF;
END $$;

DO $$
BEGIN
  IF (SELECT count(*) FROM operational_incidents WHERE clinic_id='forensic-clinic-a') <> 1 THEN
    RAISE EXCEPTION 'tenant incident read missing';
  END IF;
  IF (SELECT count(*) FROM operational_incidents WHERE clinic_id IS NULL) <> 0 THEN
    RAISE EXCEPTION 'global operational evidence leaked to tenant';
  END IF;
  BEGIN
    INSERT INTO operational_incidents(clinic_id,severity,category,summary)
    VALUES ('forensic-clinic-a','high','test','authenticated write');
    RAISE EXCEPTION 'authenticated operational evidence write accepted';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
END $$;

RESET ROLE;
ROLLBACK;
