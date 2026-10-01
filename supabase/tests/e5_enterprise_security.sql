-- E5 tenant isolation and enterprise-security metadata verification.
BEGIN;
INSERT INTO clinics(id,name,clerk_org_id) VALUES
  ('e5-tenant-a','E5 Tenant A','e5_org_a'),
  ('e5-tenant-b','E5 Tenant B','e5_org_b')
ON CONFLICT DO NOTHING;

SET ROLE authenticated;
SELECT set_config('app.clerk_org_id','e5_org_a',false);

INSERT INTO security_incidents(clinic_id,severity,category,summary)
VALUES ('e5-tenant-a','high','test','tenant A incident');
INSERT INTO security_access_reviews(clinic_id,subject_id,reviewer_id,decision)
VALUES ('e5-tenant-a','user-a','reviewer-a','approved');
INSERT INTO privacy_processing_records(clinic_id,processor_name,data_category,purpose,retention_days,deletion_method,agreement_type,agreement_status)
VALUES ('e5-tenant-a','test-processor','contact','operations',365,'secure deletion','dpa','active');
INSERT INTO data_deletion_requests(clinic_id,requested_by,scope)
VALUES ('e5-tenant-a','user-a','patient:e5-test');
INSERT INTO backup_restore_drills(clinic_id,backup_reference,started_at,result)
VALUES ('e5-tenant-a','ci-backup',now(),'planned');

DO $$
BEGIN
  IF (SELECT count(*) FROM security_incidents WHERE clinic_id='e5-tenant-b') <> 0 THEN
    RAISE EXCEPTION 'tenant B incident visible to tenant A';
  END IF;
  BEGIN
    INSERT INTO security_incidents(clinic_id,severity,category,summary)
    VALUES ('e5-tenant-b','high','test','cross-tenant write');
    RAISE EXCEPTION 'cross-tenant security incident write unexpectedly succeeded';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
END $$;

RESET ROLE;
ROLLBACK;
