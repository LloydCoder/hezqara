# HEZQARA Phase 4 — Production AI Workforce and Governed Workflow Automation

## Runtime boundary

`Frontend → API → Domain → Workflow Runtime → Agent Runtime/Tool Registry → Domain Service → Repository → Infrastructure → PostgreSQL/provider`

Workflow definitions and versions are persisted per clinic. Activated definitions are referenced immutably by workflow runs. Run and step state is server-authoritative.

## Tenant model

Clerk organization context is resolved server-side. The backend maps the organization to the provisioned clinic and sets the transaction-local PostgreSQL tenant context. Workflow tables use RLS and `FORCE ROW LEVEL SECURITY`.

## Workflow states

Definitions: `draft → active → paused → archived`.

Runs: `queued → running → waiting_for_approval → completed|failed|escalated|cancelled` with only explicit legal transitions.

## Worker boundary

Redis/Celery is used when configured. In test/development without Redis, the runtime executes synchronously so tests do not pretend a queue exists. Production without a configured worker returns an explicit unavailable error.

## AI governance

Existing agent execution remains the model boundary. Phase 4 adds an explicit tool registry with required permissions and risk classification. Model output remains untrusted input and must not directly mutate persistence or select arbitrary tools.

## Approvals

Approval decisions are server-side, tenant-scoped, permission-checked and bound to the exact approval record. Expired/non-pending approvals cannot be decided again.

## External integrations

Provider adapters remain optional. Configuration does not imply successful delivery or provider health. Unavailable providers must be surfaced as unavailable/configuration-required.

## Data protection

Synthetic fixtures only. Request IDs and workflow IDs are correlation identifiers; PHI is not used as a correlation identifier. Logs must not contain credentials, authorization headers or unnecessary model payloads.

## Phase 4 status vocabulary

Use persisted states rather than client timers or simulated activity. Future UI and agent additions should consume the same workflow, execution, approval and audit contracts.
