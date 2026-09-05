# Phase 9 AI Security Controls

## Engineering reference mapping

| Reference | HEZQARA control mapping |
|---|---|
| OWASP ASVS 5.0 | Server authorization, input validation, secure configuration, auditability and dependency hygiene. |
| OWASP API Security Top 10 | Tenant authorization, bounded pagination/resource use, SSRF boundary preservation, API inventory and safe external consumption. |
| OWASP GenAI/LLM + agentic guidance | Prompt-injection boundary, tool allowlists, output validation, data minimization, excessive agency/resource controls and fail-closed governance. |
| NIST AI RMF / GenAI Profile | Capability inventory, risk tiers, evaluation evidence, monitoring, incident/failure taxonomy and human oversight. |
| NIST SSDF | CI security gates, dependency scanning, source hygiene and reproducible testing. |
| HHS Security Rule guidance | Role-based access, authentication, audit controls, integrity and transmission-security engineering boundaries. |

These are engineering controls and design references. They are not certifications or legal compliance assertions.

## AI trust boundaries

User/browser data, patient messages, FHIR resources, provider responses and webhook payloads are untrusted inputs. Tenant authority comes from authenticated server context. AI output cannot grant itself permissions or bypass policy.

## Side-effect rule

Structured output is not sufficient for execution. Output is validated, then deterministic risk/policy checks are applied, then server authorization and approval requirements are evaluated before consequential work proceeds.

## Data minimization

Telemetry stores identifiers needed for operational lineage and avoids generic persistence of raw clinical text, patient identifiers, credentials and access tokens.
