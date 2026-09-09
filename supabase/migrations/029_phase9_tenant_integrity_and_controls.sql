-- Phase 9 closure: make governance relationships tenant-bound at the database level.
-- RLS controls visibility; these composite FKs also prevent cross-tenant references.
ALTER TABLE ai_evaluation_suites ADD CONSTRAINT ai_evaluation_suites_clinic_id_id_key UNIQUE (clinic_id,id);
ALTER TABLE ai_evaluation_cases ADD CONSTRAINT ai_evaluation_cases_clinic_id_id_key UNIQUE (clinic_id,id);
ALTER TABLE ai_evaluation_runs ADD CONSTRAINT ai_evaluation_runs_clinic_id_id_key UNIQUE (clinic_id,id);
ALTER TABLE ai_capability_versions ADD CONSTRAINT ai_capability_versions_clinic_id_id_key UNIQUE (clinic_id,id);

DO $$ DECLARE r record; BEGIN
  FOR r IN SELECT conname FROM pg_constraint WHERE conrelid='ai_evaluation_cases'::regclass AND confrelid='ai_evaluation_suites'::regclass LOOP EXECUTE format('ALTER TABLE ai_evaluation_cases DROP CONSTRAINT %I',r.conname); END LOOP;
  FOR r IN SELECT conname FROM pg_constraint WHERE conrelid='ai_evaluation_runs'::regclass AND confrelid IN ('ai_evaluation_suites'::regclass,'ai_capability_versions'::regclass) LOOP EXECUTE format('ALTER TABLE ai_evaluation_runs DROP CONSTRAINT %I',r.conname); END LOOP;
  FOR r IN SELECT conname FROM pg_constraint WHERE conrelid='ai_evaluation_results'::regclass AND confrelid IN ('ai_evaluation_runs'::regclass,'ai_evaluation_cases'::regclass) LOOP EXECUTE format('ALTER TABLE ai_evaluation_results DROP CONSTRAINT %I',r.conname); END LOOP;
END $$;

ALTER TABLE ai_evaluation_cases ADD CONSTRAINT ai_eval_cases_tenant_suite_fk FOREIGN KEY (clinic_id,suite_id) REFERENCES ai_evaluation_suites(clinic_id,id) ON DELETE CASCADE;
ALTER TABLE ai_evaluation_runs ADD CONSTRAINT ai_eval_runs_tenant_suite_fk FOREIGN KEY (clinic_id,suite_id) REFERENCES ai_evaluation_suites(clinic_id,id) ON DELETE CASCADE;
ALTER TABLE ai_evaluation_runs ADD CONSTRAINT ai_eval_runs_tenant_capability_version_fk FOREIGN KEY (clinic_id,capability_version_id) REFERENCES ai_capability_versions(clinic_id,id) ON DELETE SET NULL;
ALTER TABLE ai_evaluation_results ADD CONSTRAINT ai_eval_results_tenant_run_fk FOREIGN KEY (clinic_id,run_id) REFERENCES ai_evaluation_runs(clinic_id,id) ON DELETE CASCADE;
ALTER TABLE ai_evaluation_results ADD CONSTRAINT ai_eval_results_tenant_case_fk FOREIGN KEY (clinic_id,case_id) REFERENCES ai_evaluation_cases(clinic_id,id) ON DELETE CASCADE;

-- Correctness constraints for commercial/scale primitives.
ALTER TABLE platform_jobs DROP CONSTRAINT IF EXISTS platform_jobs_idempotency_key_key;
