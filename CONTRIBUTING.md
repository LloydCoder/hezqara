# Contributing to HEZQARA

HEZQARA is proprietary software. Contributions are accepted only from authorized contributors and under the repository's contribution and intellectual-property arrangements.

## Before changing code

1. Read README.md and the relevant architecture/security documentation.
2. Identify the tenant, authorization, data, AI-governance and operational boundaries affected by the change.
3. Never use real patient data, credentials or production secrets.
4. Preserve database-enforced controls; do not move security decisions into the browser.
5. Update documentation when behavior, configuration, architecture or operational requirements change.

## Required engineering standards

Changes must preserve:

- server-side authentication and authorization;
- tenant isolation and PostgreSQL RLS/FORCE RLS;
- deterministic validation for security-sensitive state;
- AI governance and approval boundaries;
- idempotency and durable execution semantics;
- signed webhook and replay protections;
- safe secret handling;
- migration determinism and backward/forward deployment safety where applicable;
- accessible and type-safe frontend behavior.

## Tests

Run the smallest relevant local checks before opening a pull request. CI remains authoritative.

Frontend checks include lint, type-check, production build and E2E where applicable.

Backend checks include compilation/import validation, unit/integration tests and database/RLS validation where applicable.

Security checks include dependency scanning, secret scanning and SBOM generation.

Do not disable, weaken or bypass a security or validation gate to make a pull request green.

## Pull requests

Describe:

- what changed;
- why it changed;
- security/tenant impact;
- migration impact;
- configuration changes;
- test evidence;
- documentation changes;
- any deployment or provider prerequisites.

Keep debugging branches and obsolete diagnostic pull requests closed once their work has been incorporated into the canonical branch.

## Healthcare safety

Synthetic data is mandatory for CI, fixtures and examples. Do not place PHI/ePHI in source code, logs, tests, issues, screenshots or pull-request descriptions.

HEZQARA is not a clinical decision-maker. Consequential workflows must retain the documented governance and human-approval controls.

## License and third-party code

The repository is proprietary and governed by LICENSE. Third-party packages and externally sourced code remain subject to their own licenses. Do not copy code into the repository unless its licensing terms permit the intended use.
