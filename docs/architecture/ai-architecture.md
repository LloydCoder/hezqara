# AI architecture

Agents implement a common workforce contract. Execution carries tenant, user, permissions, patient context when permitted, execution ID, idempotency key and a tenant-scoped governance service.

The canonical execution boundary is:

```
tenant/authz
  → capability/version
  → policy + risk
  → data/tool authorization
  → provider/model
  → deterministic output validation
  → action/risk re-evaluation
  → approval/escalation
  → governed side effect
  → audit/telemetry
```

Policies execute before models/tools. AI outputs are untrusted data. Authorization and tenant isolation are never delegated to an LLM.

The agent runtime fails closed if governance is absent. A tool call must satisfy both user permissions and governance policy, and consequential side effects require the side-effect authorization gate. Approval-required actions are not treated as completed until an approved authorization is verified.

Healthcare message classification is governed through the same tenant policy boundary; clinical classifications always retain human review.

This architecture follows the runtime-control direction of the OWASP Agent Control Standard and the complete-mediation principle described in OWASP's agentic security guidance.
