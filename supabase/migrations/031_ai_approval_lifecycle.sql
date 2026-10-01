-- Phase 9 closure: durable AI approval lifecycle metadata.
-- Approvals are tenant-scoped and auditable. No approval endpoint may infer
-- completion of an external side effect from an approval decision alone.
ALTER TABLE public.ai_approvals
  ADD COLUMN IF NOT EXISTS decided_by TEXT,
  ADD COLUMN IF NOT EXISTS decision_reason TEXT,
  ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_ai_approvals_clinic_pending
  ON public.ai_approvals (clinic_id, decision, created_at DESC)
  WHERE decision = 'pending';

CREATE INDEX IF NOT EXISTS idx_ai_approvals_execution
  ON public.ai_approvals (clinic_id, execution_id, created_at DESC);
