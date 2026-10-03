# E16 Architecture — Documentation Intelligence

E16 consumes Hezqara clinical-documentation outputs; it does not replace the E15 clinician approval boundary.

Flow:

encounter → transcript → draft → clinician review/approval → documentation intelligence → human-reviewable evidence/workflow signals.

The E16 persistence model is tenant-scoped through clinic composite foreign keys and PostgreSQL RLS/FORCE RLS. Every proposed fact records an extractor version and source reference. Quality checks are explicit records rather than hidden model prose.

The initial implementation deliberately uses deterministic section checks and the already-approved structured note output. More advanced longitudinal extraction can be added within E16 without changing the authority boundary.
