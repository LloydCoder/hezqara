# Changelog

All notable HEZQARA changes are documented here. Release notes follow the Keep a Changelog structure. Version numbers follow Semantic Versioning where applicable.

## [Unreleased]

### Security
- Remediate the frontend dependency audit gate for the 2026 `braces` stack-overflow advisory and PostCSS selector-parser CPU-exhaustion advisory.
- Record the temporary upstream fork override for `braces` so the security rationale remains auditable until an upstream patched release is published.

### Documentation
- Add repository community-health files, issue forms, LLM documentation indexes, and release-oriented documentation navigation.
- Clarify the distinction between repository verification and external healthcare/regulatory certification.

## [1.0.0]

- First tagged HEZQARA release.
- E1–E8 production-proving and post-E8 forensic hardening evidence.
- E9–E24 enterprise implementation and validation sequence.
- Multi-tenant authorization and PostgreSQL RLS/FORCE RLS controls.
- Governed AI execution, approval, validation, audit and telemetry boundaries.
- FHIR R4 and SMART App Launch interoperability boundaries.
- Commercial controls, durable execution, reliability, security and operational evidence.

[Unreleased]: https://github.com/LloydCoder/hezqara/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/LloydCoder/hezqara/releases/tag/v1.0.0
