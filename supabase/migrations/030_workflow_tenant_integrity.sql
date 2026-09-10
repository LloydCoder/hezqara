-- Phase 4 integrity hardening.
-- Make workflow relationships tenant-consistent at the database layer, not only through RLS.
-- Existing rows are backfilled before NOT NULL/composite foreign keys are installed.

ALTER TABLE public.workflow_versions
  ADD COLUMN IF NOT EXISTS clinic_id TEXT;

UPDATE public.workflow_versions wv
SET clinic_id = w.clinic_id
FROM public.workflows w
WHERE w.id = wv.workflow_id
  AND wv.clinic_id IS NULL;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM public.workflow_versions WHERE clinic_id IS NULL) THEN
    RAISE EXCEPTION 'workflow_versions contains rows without a tenant';
  END IF;
END $$;

ALTER TABLE public.workflow_versions
  ALTER COLUMN clinic_id SET NOT NULL;

ALTER TABLE public.workflow_versions
  DROP CONSTRAINT IF EXISTS workflow_versions_workflow_id_fkey;

ALTER TABLE public.workflow_versions
  ADD CONSTRAINT workflow_versions_clinic_id_id_key UNIQUE (clinic_id, id);

ALTER TABLE public.workflow_versions
  ADD CONSTRAINT workflow_versions_clinic_workflow_fk
  FOREIGN KEY (clinic_id, workflow_id)
  REFERENCES public.workflows (clinic_id, id)
  ON DELETE CASCADE;

ALTER TABLE public.workflow_runs
  DROP CONSTRAINT IF EXISTS workflow_runs_workflow_id_fkey,
  DROP CONSTRAINT IF EXISTS workflow_runs_workflow_version_id_fkey;

ALTER TABLE public.workflow_runs
  ADD CONSTRAINT workflow_runs_clinic_workflow_fk
  FOREIGN KEY (clinic_id, workflow_id)
  REFERENCES public.workflows (clinic_id, id)
  ON DELETE RESTRICT,
  ADD CONSTRAINT workflow_runs_clinic_version_fk
  FOREIGN KEY (clinic_id, workflow_version_id)
  REFERENCES public.workflow_versions (clinic_id, id)
  ON DELETE RESTRICT;

ALTER TABLE public.workflow_step_runs
  ADD COLUMN IF NOT EXISTS clinic_id TEXT;

UPDATE public.workflow_step_runs wsr
SET clinic_id = wr.clinic_id
FROM public.workflow_runs wr
WHERE wr.id = wsr.workflow_run_id
  AND wsr.clinic_id IS NULL;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM public.workflow_step_runs WHERE clinic_id IS NULL) THEN
    RAISE EXCEPTION 'workflow_step_runs contains rows without a tenant';
  END IF;
END $$;

ALTER TABLE public.workflow_step_runs
  ALTER COLUMN clinic_id SET NOT NULL;

ALTER TABLE public.workflow_step_runs
  DROP CONSTRAINT IF EXISTS workflow_step_runs_workflow_run_id_fkey;

ALTER TABLE public.workflow_step_runs
  ADD CONSTRAINT workflow_step_runs_clinic_id_id_key UNIQUE (clinic_id, id),
  ADD CONSTRAINT workflow_step_runs_clinic_run_fk
  FOREIGN KEY (clinic_id, workflow_run_id)
  REFERENCES public.workflow_runs (clinic_id, id)
  ON DELETE CASCADE;

ALTER TABLE public.workflow_approvals
  DROP CONSTRAINT IF EXISTS workflow_approvals_workflow_run_id_fkey,
  DROP CONSTRAINT IF EXISTS workflow_approvals_workflow_step_run_id_fkey;

ALTER TABLE public.workflow_approvals
  ADD CONSTRAINT workflow_approvals_clinic_run_fk
  FOREIGN KEY (clinic_id, workflow_run_id)
  REFERENCES public.workflow_runs (clinic_id, id)
  ON DELETE CASCADE,
  ADD CONSTRAINT workflow_approvals_clinic_step_fk
  FOREIGN KEY (clinic_id, workflow_step_run_id)
  REFERENCES public.workflow_step_runs (clinic_id, id)
  ON DELETE CASCADE;

ALTER TABLE public.workflow_events
  DROP CONSTRAINT IF EXISTS workflow_events_workflow_run_id_fkey;

ALTER TABLE public.workflow_events
  ADD CONSTRAINT workflow_events_clinic_run_fk
  FOREIGN KEY (clinic_id, workflow_run_id)
  REFERENCES public.workflow_runs (clinic_id, id)
  ON DELETE CASCADE;

-- Communications also carries both tenant and workflow identifiers; bind that
-- relationship to the same tenant boundary to prevent cross-tenant references.
ALTER TABLE public.communications
  DROP CONSTRAINT IF EXISTS communications_workflow_run_id_fkey;

ALTER TABLE public.communications
  ADD CONSTRAINT communications_clinic_workflow_run_fk
  FOREIGN KEY (clinic_id, workflow_run_id)
  REFERENCES public.workflow_runs (clinic_id, id)
  ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_workflow_versions_clinic_id
  ON public.workflow_versions (clinic_id, id);
CREATE INDEX IF NOT EXISTS idx_workflow_step_runs_clinic_id
  ON public.workflow_step_runs (clinic_id, id);

COMMENT ON COLUMN public.workflow_versions.clinic_id IS 'Tenant owner; must match the referenced workflow tenant.';
COMMENT ON COLUMN public.workflow_step_runs.clinic_id IS 'Tenant owner; must match the referenced workflow run tenant.';
