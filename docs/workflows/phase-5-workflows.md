# Phase 5 Workflows

Supported Phase 5 step types:

- `create_task`
- `complete`
- `classify_message`
- `update_appointment`
- `send_communication`
- `request_approval`

Every workflow is versioned and tenant scoped. Runs use an idempotency key and persist step state. Execution is bounded to 25 steps. Approval steps pause the run and can be resumed only after a valid server-side approval.

Communication steps persist a communication and outbox event in the same transaction. A worker then dispatches the external side effect and records provider evidence.
