# E20 — AI Governance, MCP & Clinical Documentation Safety

Status: IMPLEMENTED — awaiting CI/evidence gate.

MCP is treated as a transport/interface, never as the authorization boundary. Tool policies are tenant-scoped and classify interface, risk, side effects, approval, idempotency and allowed data/actions.

High-risk side effects require explicit approval. Tool calls outside tenant scope or allowlists are blocked. Clinical documentation remains clinician-authoritative.
