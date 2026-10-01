# Phase 9 — AI Reliability, Evaluation & Governance

## E1 closure contract

Every real AI execution path must pass through a tenant-scoped governance service before model use and again after model output, with consequential tool/API side effects requiring a second authorization barrier.

The enforced runtime sequence is:

```
authenticated tenant
  ↓
server authorization
  ↓
capability
  ↓
active capability version
  ↓
active policy
  ↓
input/data-class controls
  ↓
tool allowlist
  ↓
provider availability
  ↓
model execution
  ↓
deterministic output validation
  ↓
action/risk re-evaluation
  ↓
approval or escalation gate
  ↓
governed side-effect authorization
  ↓
audit + telemetry
```

The LLM is never an authority source. It cannot grant permissions, select a broader tenant scope, approve its own high-impact action, or bypass server policy.

### Runtime enforcement

`AgentExecutor` fails closed if no tenant-scoped `AIGovernanceService` is supplied. It performs a pre-model policy decision and a post-output policy decision. A denied, escalated, or approval-required decision cannot return a completed execution.

Declared tools are checked against both the authenticated user's permissions and the capability/policy tool allowlist. The executor exposes a governed tool-call boundary; consequential tool calls must use `authorize_side_effect`, which verifies an approved, unexpired human approval for approval-required actions.

The API retains a defense-in-depth preflight and persists policy decisions, telemetry, approvals and audit events.

### Secondary AI paths

Healthcare message classification is also fail-closed: `MessageIntelligence` requires the tenant governance service and performs a policy decision before classification. Clinical classifications are required to escalate to human review and cannot become autonomous clinical decisions.

### Risk tiers

- **0 — Informational:** no side effect.
- **1 — Administrative:** bounded recommendation.
- **2 — Operational:** deterministic policy gate and authorized execution.
- **3 — High-impact administrative:** mandatory human approval.
- **4 — Clinical/high-impact:** autonomous decision is denied.

### Failure taxonomy

`INPUT_INVALID`, `CONTEXT_MISSING`, `MODEL_TIMEOUT`, `MODEL_UNAVAILABLE`, `OUTPUT_INVALID`, `OUTPUT_UNGROUNDED`, `POLICY_DENIED`, `TOOL_DENIED`, `AUTHORIZATION_DENIED`, `PHI_BOUNDARY_VIOLATION`, `PROMPT_INJECTION_DETECTED`, `CONFIDENCE_TOO_LOW`, `HUMAN_APPROVAL_REQUIRED`, `INTEGRATION_FAILURE`, `RATE_LIMITED`, `UNKNOWN`.

## Adversarial proof obligations

The E1 test suite proves at minimum:

1. AI execution without tenant governance fails closed.
2. A policy denial occurs before model invocation.
3. Model output cannot bypass a second policy decision.
4. Approval-required actions cannot complete autonomously.
5. Tool calls require both user permission and governance authorization.
6. A governed tool call is blocked when policy denies the side effect.
7. Healthcare message classification cannot execute without governance.
8. Clinical message classification cannot clear the human-review requirement.

## Registry and versioning

The Phase 9 schema records capability metadata and capability versions independently. Versioned records cover prompt, system instruction, tool policy, output schema and evaluation suite. Versions are immutable by convention once used in an execution; a new behavior requires a new version.

## Evaluation

Evaluation suites and cases are tenant scoped and versioned. The deterministic evaluation engine validates structured output, expected administrative actions and evidence requirements. The repository's golden dataset is synthetic-only. No benchmark is reported without persisted observations.

## Observability

Telemetry stores operational lineage and minimizes content. Generic telemetry does not require raw patient messages, clinical notes, credentials or access tokens. Policy decisions, failure events and approvals are separately queryable.

## Emergency controls

Tenant-scoped controls can disable AI, force human approval, force deterministic fallback, disable selected capabilities/providers, or disable tool access. Control mutations require governance-management permission and are audited.

## Provider behavior

Provider availability is distinct from configuration. Timeout, malformed output, rate limiting and unavailable-provider paths must fail closed or escalate. Provider switching must not silently change the risk profile.

## Security references

OWASP's Agentic Applications guidance emphasizes runtime controls for goal hijacking, tool misuse, identity/privilege abuse, supply-chain risk, unexpected code execution and cascading failures. OWASP's September 2026 Agent Control Standard further emphasizes inspectable, traceable, instrumentable agents and runtime policy-enforcement hooks. NIST AI RMF/GenAI Profile provides the lifecycle risk-management reference.

These are engineering references, not certifications or legal compliance claims.
