# E16 Architecture — Documentation Intelligence

E16 consumes Hezqara clinical-documentation outputs; it does not replace the E15 clinician approval boundary.

Flow:

encounter → transcript → draft → clinician review/approval → documentation intelligence → human-reviewable evidence/workflow signals.

The persistence model is tenant-scoped through composite clinic keys and PostgreSQL RLS/FORCE RLS. Every quality check and insight carries versioned ruleset/model metadata and source references. Insights remain proposed until explicitly reviewed.

The initial implementation is intentionally deterministic: it checks expected documentation sections, surfaces follow-up language and uncertainty, and records findings as reviewable evidence. It does not diagnose, prescribe, triage, or commit clinical actions.
