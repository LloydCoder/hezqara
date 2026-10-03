-- E16 database proof: documentation intelligence tenant isolation.
BEGIN;

INSERT INTO clinics(id,name,clerk_org_id) VALUES
 ('ci-e16-a','CI E16 A','ci_e16_org_a'),
 ('ci-e16-b','CI E16 B','ci_e16_org_b')
ON CONFLICT (id) DO NOTHING;

INSERT INTO documentation_quality_checks(id,clinic_id,source_type,score,summary)
VALUES ('ci-e16-check-a','ci-e16-a','clinical_note',0.85,'{"warning_count":1}')
ON CONFLICT (id) DO NOTHING;

INSERT INTO documentation_insights(id,clinic_id,quality_check_id,kind,key,detail,severity,confidence)
VALUES ('ci-e16-insight-a','ci-e16-a','ci-e16-check-a','completeness','missing_plan','Plan section is missing.','warning',0.98)
ON CONFLICT (id) DO NOTHING;

SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','ci_e16_org_a',false);

DO 'BEGIN
  IF NOT EXISTS (SELECT 1 FROM documentation_insights WHERE id=''ci-e16-insight-a'') THEN
    RAISE EXCEPTION ''tenant A cannot read its own E16 insight'';
  END IF;
END';

SELECT set_config('app.clerk_org_id','ci-e16_org_b',false);

DO 'BEGIN
  IF EXISTS (SELECT 1 FROM documentation_quality_checks WHERE id=''ci-e16-check-a'') THEN
    RAISE EXCEPTION ''cross-tenant E16 quality-check read'';
  END IF;
  IF EXISTS (SELECT 1 FROM documentation_insights WHERE id=''ci-e16-insight-a'') THEN
    RAISE EXCEPTION ''cross-tenant E16 insight read'';
  END IF;
END;

RESET ROLE;
ROLLBACK;
