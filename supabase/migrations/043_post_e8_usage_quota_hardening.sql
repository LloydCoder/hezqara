-- Post-E8 forensic hardening: tenant usage is quota-controlled at the
-- database boundary so a client cannot bypass commercial limits by writing
-- usage rows directly.

CREATE OR REPLACE FUNCTION public.enforce_platform_usage_limit()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  limit_value bigint;
BEGIN
  IF NEW.quantity < 0 THEN
    RAISE EXCEPTION 'usage quantity cannot be negative' USING ERRCODE='check_violation';
  END IF;

  SELECT CASE NEW.metric
    WHEN 'executions' THEN monthly_executions
    WHEN 'voice_minutes' THEN monthly_voice_minutes
    WHEN 'messages' THEN monthly_messages
    ELSE NULL
  END
  INTO limit_value
  FROM public.tenant_limits
  WHERE clinic_id=NEW.clinic_id;

  IF limit_value IS NULL THEN
    limit_value := CASE NEW.metric
      WHEN 'executions' THEN 1000
      WHEN 'voice_minutes' THEN 500
      WHEN 'messages' THEN 5000
      ELSE NULL
    END;
  END IF;

  IF limit_value IS NULL THEN
    RAISE EXCEPTION 'unsupported usage metric: %', NEW.metric USING ERRCODE='check_violation';
  END IF;

  IF NEW.quantity > limit_value THEN
    RAISE EXCEPTION 'usage quota exceeded for metric %: % > %', NEW.metric, NEW.quantity, limit_value USING ERRCODE='check_violation';
  END IF;

  RETURN NEW;
END;
$$;

REVOKE ALL ON FUNCTION public.enforce_platform_usage_limit() FROM PUBLIC;

DROP TRIGGER IF EXISTS platform_usage_limit_guard ON public.platform_usage_daily;
CREATE TRIGGER platform_usage_limit_guard
BEFORE INSERT OR UPDATE OF quantity,metric,clinic_id
ON public.platform_usage_daily
FOR EACH ROW
EXECUTE FUNCTION public.enforce_platform_usage_limit();

COMMENT ON FUNCTION public.enforce_platform_usage_limit()
IS 'Server-side quota guard for tenant usage. Provider/service code must still stop work before consuming paid resources; this trigger is a final accounting boundary.';
