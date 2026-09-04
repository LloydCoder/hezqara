# AI architecture

Agents implement a common workforce contract. Execution carries tenant, user, permissions, patient context when permitted, execution ID and idempotency key. Policies execute before tools/models. Model providers are adapters, not dependencies of domain agents.

AI outputs are untrusted data. Structured validation, deterministic policy checks, confidence/escalation and audit events are required before consequential actions. Authorization and tenant isolation are never delegated to an LLM.
