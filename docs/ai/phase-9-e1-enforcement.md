# E1 AI Governance Enforcement Evidence

This file is the durable audit index for Phase 9 E1. It is intentionally evidence-oriented: an implemented control is not marked verified until the repository CI gates execute successfully.

## Control chain

Authenticated tenant → server authorization → capability/version → policy/risk → data/tool authorization → provider/model → deterministic validation → action/risk re-evaluation → approval/escalation → side-effect authorization → audit/telemetry.

## Runtime entry points

- Workforce model execution: `backend/app/ai/orchestration/executor.py`
- Authenticated execution API: `backend/app/api/v1/executions.py`
- Healthcare message AI: `backend/app/domains/patient_engagement/ai.py`
- Workflow AI classification: `backend/app/domains/workflows/runtime.py`
- Governance policy engine: `backend/app/ai/governance/service.py`
- Governance contracts: `backend/app/ai/governance/contracts.py`

## Adversarial cases

- Missing governance → fail closed.
- Pre-model policy denial → provider is not called.
- Approval-required policy → proposal may be generated, but completion/side effect remains blocked.
- Post-output action drift → re-evaluated against current governance.
- Tool without user permission → blocked.
- Tool outside governance allowlist → blocked.
- Side effect without valid approval → blocked.
- Secondary AI path without governance → fail closed.
- Clinical classification → human review retained.

## Verification state

E1 remains **validation-gated** until the complete GitHub Actions workflow is green. No production-readiness claim is made by this document.
