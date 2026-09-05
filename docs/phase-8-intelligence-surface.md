# HEZQARA Phase 8 — Intelligence Surface

## Scope

Phase 8 derives decision-support intelligence from tenant-scoped operational data. It does not introduce a warehouse, synthetic metrics, clinical decision autonomy, or compliance certification claims.

### Surfaces

- **Operational trends** — daily calls, bookings, completions, no-shows, tasks, AI execution/escalation, workflows and communications.
- **Revenue-cycle intelligence** — charges, payments, claims billed/paid, denials, open A/R, collection rate and denial rate.
- **Insurance intelligence** — eligibility request/verification/failure, authorization submission/approval/denial and referral completion.
- **Compliance evidence** — audit event summaries plus paginated evidence exploration.
- **Executive intelligence** — deterministic risk signals sourced from canonical metrics; no LLM-generated KPI values.
- **Drill-down/source tracing** — metric-level trace endpoints return source table, time field, day/status and aggregate contribution. Raw patient/PHI fields are not exported through analytics traces.
- **Governed exports** — CSV export uses a fixed non-PHI field allowlist, a maximum 366-day window, `analytics:export` permission, no-store response semantics, and an immutable audit event for the export request.
- **Metric catalog** — each metric declares definition, formula, source tables, time semantics, denominator, null behavior, permission, PHI flag and drill-down resource.

## Data contract

`source tables -> canonical metric definition -> authorized repository query -> service calculation -> typed API -> design-system UI`

Financial and rate calculations are deterministic. A rate is `null` when its denominator is zero or otherwise undefined; the UI renders this as `—` rather than fabricating a zero. Reporting windows use an inclusive start / exclusive end (`start <= timestamp < end`) and are UTC-normalized. Maximum reporting window is 366 days.

## Security model

All analytics requests require authenticated tenant context. Database work is performed through `tenant_session_context`, which sets the organization transaction context and uses the `authenticated` database role so existing RLS policies remain authoritative.

Export is intentionally stronger than read access: owner/admin/manager roles receive `analytics:export` by default; staff/viewer roles do not receive it by default; explicit Clerk `org_permissions` claims remain authoritative; and export requests are recorded with actor, tenant, request id, time window, fields and row count. The export field set contains aggregate operational/revenue/insurance values only and excludes patient identifiers and free-form clinical content.

Compliance evidence is read with `compliance:read`. Compliance metric tracing additionally requires `compliance:read` even when the caller already has `analytics:read`.

## Performance

Daily operational aggregation uses per-source grouped CTEs joined to a generated day series rather than one correlated subquery per metric per day. Phase 8 adds tenant/time/status indexes for high-volume analytical sources and audit exploration. A warehouse or materialized view should only be introduced after production query plans demonstrate a need.

## AI governance

Executive risk signals are deterministic threshold evaluations over canonical metrics. The executive endpoint does not pass raw database records to an LLM and does not allow an LLM to invent metric values. This supports the NIST AI RMF / GenAI Profile principle of governed, measurable AI risk management while keeping Phase 8 KPI computation non-generative.

## Healthcare interoperability context

The intelligence model remains compatible with the existing FHIR/integration boundary. CMS's 2024 Interoperability and Prior Authorization final rule requires affected payers to use FHIR-based APIs and establishes prior-authorization API requirements; HEZQARA's analytics layer treats those integration events as source evidence rather than asserting payer compliance itself.

## External standards used as engineering references

- OWASP ASVS 5.0.0 for web application verification.
- OWASP API Security Top 10 (2023) for authorization, resource-consumption, SSRF, inventory and unsafe-consumption risks.
- NIST AI RMF and NIST AI 600-1 GenAI Profile for AI governance.
- HHS HIPAA Security Rule guidance for access control and audit controls.
- HL7 FHIR R4 and applicable CMS interoperability guidance for the healthcare integration context.

These references are engineering controls and design inputs, not evidence that HEZQARA is certified or legally compliant.
