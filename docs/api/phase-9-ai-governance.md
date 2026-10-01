# Phase 9 AI Governance API

All endpoints use the existing Clerk-authenticated tenant context and server-side permission checks.

## Read endpoints

- `GET /api/v1/ai-governance/summary`
- `GET /api/v1/ai-governance/capabilities`
- `GET /api/v1/ai-governance/capabilities/{capability_id}`
- `GET /api/v1/ai-governance/telemetry`
- `GET /api/v1/ai-governance/failures`
- `GET /api/v1/ai-governance/approvals`
- `GET /api/v1/ai-governance/controls`
- `GET /api/v1/ai-governance/evaluation/suites`
- `GET /api/v1/ai-governance/evaluation/cases?suite_id=...`

## Management endpoints

- `PUT /api/v1/ai-governance/controls`
- `POST /api/v1/ai-governance/evaluation/suites`
- `POST /api/v1/ai-governance/evaluation/cases`
- `POST /api/v1/ai-governance/evaluation/runs?suite_id=...`
- `POST /api/v1/ai-governance/evaluation/results`

Governance reads require `ai:governance:read`; control and evaluation mutations require `ai:governance:manage`. Pagination is bounded to 100 records per request.

The API does not accept a browser-supplied tenant ID as authority. Sensitive governance mutations are audited. Evaluation results must contain observed evidence; no endpoint manufactures benchmark results.
