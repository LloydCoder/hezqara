# Phase 9 AI Security Controls

## Engineering reference mapping

| Reference | HEZQARA control mapping |
|---|---|
| OWASP ASVS 5.0 | Server authorization, input validation, secure configuration, auditability and dependency hygiene. |
| OWASP API Security Top 10 | Tenant authorization, bounded pagination/resource use, SSRF boundary preservation, API inventory and safe external consumption. |
| OWASP GenAI/LLM + Agentic guidance | Prompt-injection boundary, goal/scope validation, tool allowlists, output validation, data minimization, excessive-agency controls and fail-closed governance. |
| OWASP Agent Control Standard (ACS) | Runtime enforcement hook at the agent/tool boundary, inspectability, traceability, instrumentation and portable policy enforcement. |
| NIST AI RMF / GenAI Profile | Capability inventory, risk tiers, evaluation evidence, monitoring, incident/failure taxonomy and human oversight. |
| NIST SSDF | CI security gates, dependency scanning, source hygiene and reproducible testing. |
| HHS Security Rule guidance | Role-based access, authentication, audit controls, integrity and transmission-security engineering boundaries. |

These are engineering controls and design references. They are not certifications or legal compliance assertions.

## AI trust boundaries

User/browser data, patient messages, FHIR resources, provider responses and webhook payloads are untrusted inputs. Tenant authority comes from authenticated server context. AI output cannot grant itself permissions or bypass policy.

## Complete-mediation rule

Every model invocation requires a tenant-scoped governance decision. Every consequential tool/API side effect requires a second deterministic authorization decision at the side-effect boundary. High-impact actions require a valid, unexpired human approval before the side effect is permitted.

The governance service therefore separates:

- **policy decision** — whether the proposed action is allowed;
- **approval state** — whether a human has approved an approval-required action;
- **side-effect authorization** — whether the exact execution/action/policy combination is permitted to proceed.

## Data minimization

Telemetry stores identifiers needed for operational lineage and avoids generic persistence of raw clinical text, patient identifiers, credentials and access tokens.

## E1 adversarial coverage

The enforcement suite covers missing-governance fail-closed behavior, pre-model policy denial, post-model action re-evaluation, approval-required blocking, governed tool denial and the secondary healthcare message-classification path.
