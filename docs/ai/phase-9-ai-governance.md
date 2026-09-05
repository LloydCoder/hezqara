# Phase 9 — AI Reliability, Evaluation & Governance

## Governance contract

Every production AI execution is attributable to a tenant, capability, capability version, prompt version, model/provider, validation result, policy decision, risk tier and outcome. Consequential actions are bounded by server authorization and human approval where policy requires it.

### Risk tiers

- **0 — Informational:** no side effect.
- **1 — Administrative:** bounded recommendation.
- **2 — Operational:** deterministic policy gate and authorized execution.
- **3 — High-impact administrative:** mandatory human approval.
- **4 — Clinical/high-impact:** autonomous decision is denied.

### Failure taxonomy

`INPUT_INVALID`, `CONTEXT_MISSING`, `MODEL_TIMEOUT`, `MODEL_UNAVAILABLE`, `OUTPUT_INVALID`, `OUTPUT_UNGROUNDED`, `POLICY_DENIED`, `TOOL_DENIED`, `AUTHORIZATION_DENIED`, `PHI_BOUNDARY_VIOLATION`, `PROMPT_INJECTION_DETECTED`, `CONFIDENCE_TOO_LOW`, `HUMAN_APPROVAL_REQUIRED`, `INTEGRATION_FAILURE`, `RATE_LIMITED`, `UNKNOWN`.

## Registry and versioning

The Phase 9 schema records capability metadata and capability versions independently. Versioned records cover prompt, system instruction, tool policy, output schema and evaluation suite. Versions are immutable by convention once used in an execution; a new behavior requires a new version.

## Evaluation

Evaluation suites and cases are tenant scoped and versioned. The deterministic evaluation engine validates structured output, expected administrative actions and evidence requirements. The repository's golden dataset is synthetic-only. No benchmark is reported without persisted observations.

## Observability

Telemetry stores operational lineage and minimizes content. Generic telemetry does not require raw patient messages, clinical notes, credentials or access tokens. Failure events and policy decisions are separately queryable.

## Emergency controls

Tenant-scoped controls can disable AI, force human approval, force deterministic fallback, disable selected capabilities/providers, or disable tool access. Control mutations require governance-management permission and are audited.

## Provider behavior

Provider availability is distinct from configuration. Timeout, malformed output, rate limiting and unavailable-provider paths must fail closed or escalate. Provider switching must not silently change the risk profile.

## Security references

OWASP ASVS 5.0, OWASP API Security Top 10, OWASP GenAI/LLM and agentic-AI guidance, NIST AI RMF and GenAI Profile, NIST SSDF, HHS Security Rule engineering controls, and healthcare interoperability/FHIR guidance are used as engineering references. HEZQARA does not claim HIPAA, GDPR, FHIR, CMS or other certification from these controls.
