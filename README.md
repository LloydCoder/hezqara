# HEZQARA

> Governed AI workforce infrastructure for healthcare operations, designed to automate administrative work while keeping authorization, human oversight, and accountability explicit.

<p align="center">
  <a href="https://github.com/LloydCoder/hezqara/actions/workflows/ci.yml"><img src="https://github.com/LloydCoder/hezqara/actions/workflows/ci.yml/badge.svg" alt="HEZQARA CI"></a>
  <a href="https://github.com/LloydCoder/hezqara/actions/workflows/security.yml"><img src="https://github.com/LloydCoder/hezqara/actions/workflows/security.yml/badge.svg" alt="HEZQARA Security"></a>
  <a href="https://github.com/LloydCoder/hezqara/actions/workflows/e8-production-proving.yml"><img src="https://github.com/LloydCoder/hezqara/actions/workflows/e8-production-proving.yml/badge.svg" alt="Production proving"></a>
</p>

> [!IMPORTANT]
> HEZQARA is proprietary software. Repository validation is engineering evidence; it is not, by itself, HIPAA, GDPR, NDPA, SOC 2, ISO 27001, FHIR/SMART certification, clinical efficacy, customer ROI, or production-scale proof.

## Why HEZQARA

Healthcare teams have large volumes of administrative work but cannot safely treat an AI model as an authorization authority. HEZQARA puts the operating controls around AI workers:

| Principle | HEZQARA approach |
|---|---|
| Tenant isolation | Authenticated organization context, server authorization, domain boundaries and PostgreSQL RLS/FORCE RLS |
| Human control | Policy, confidence and approval boundaries for consequential workflows |
| Accountability | Audit/evidence trails for governed execution and operational state |
| Interoperability | Explicit FHIR R4 4.0.1 and SMART App Launch 2.2.0 boundaries |
| Reliability | PostgreSQL-backed authority with Redis/Celery delivery and recovery controls |
| Commercial control | Subscription, entitlement, usage and quota boundaries |

HEZQARA is an administrative operations platform. It does not replace an EHR and is not a diagnosis, triage, symptom-checker, treatment-decision, or prescribing engine. AI Scribe functionality is draft-oriented and requires clinician review, editing and approval.

## Visual proof

A production UI screenshot/demo is intentionally not fabricated in documentation. Add an approved product screenshot or short demo to this section when a current, representative asset is available.

## Quick start

The fastest way to inspect the frontend locally is:

~~~bash
git clone https://github.com/LloydCoder/hezqara.git
cd hezqara/frontend
cp .env.example .env.local
npm ci
npm run dev
~~~

Open http://localhost:3004.

The application can render without Clerk configuration, but authenticated workflows require the corresponding Clerk environment variables. Never put server secrets in NEXT_PUBLIC_* variables.

## Installation

### Frontend

Prerequisites:

- Node.js 24.x
- npm with the repository lockfile

~~~bash
cd frontend
npm ci
~~~

Production build:

~~~bash
npm run lint
npm run type-check
npm run build
npm run start
~~~

### Backend

Prerequisites:

- Python 3.12+
- PostgreSQL/Supabase for database-backed validation
- Redis for worker/durable-delivery paths

~~~bash
cd backend
python -m pip install -r requirements.txt
pytest -q
~~~

### Full development topology

The complete stack can include PostgreSQL/Supabase, Redis, FastAPI, Celery worker/beat, and the Next.js frontend. CI provisions the services required for its validation paths. Production healthcare data must never be used in local, preview, benchmark, or CI environments.

## Usage

### Frontend

~~~bash
cd frontend
npm run dev
~~~

### Backend

~~~bash
cd backend
PYTHONPATH=. APP_ENV=development uvicorn app.main:app --reload --port 8000
~~~

### Verification

~~~bash
cd frontend
npm run lint
npm run type-check
npm run build
~~~

Backend, database/RLS, E2E, security and production-proving checks are defined by the GitHub Actions workflows.

## Configuration

| Area | Source | Notes |
|---|---|---|
| Frontend | frontend/.env.example | Browser-visible NEXT_PUBLIC_* values must contain no secrets |
| Backend | backend/.env.example | Server-side credentials and provider secrets |
| Database | Supabase/PostgreSQL configuration | RLS/FORCE RLS remains authoritative |
| Authentication | Clerk Organizations | Server-side organization/tenant context is authoritative |
| AI providers | Backend configuration | Provider keys remain server-side |
| Billing | Stripe boundary | Webhook signatures and replay controls apply |
| Deployment | vercel.json and docs/operations/ | Vercel is the frontend target; API/workers/database have separate runtime requirements |

## Architecture

~~~text
Browser
  │
  ▼
Clerk organization identity
  │
  ▼
Verified TenantContext
  │
  ▼
Server authorization
  │
  ▼
FastAPI domain/API layer
  ├── AI governance → policy → approval → execution → validation → audit
  ├── Healthcare integrations → FHIR/SMART adapter boundaries
  ├── Durable execution → PostgreSQL authority + Redis/Celery delivery
  └── Commercial controls → subscriptions → entitlements → usage/quota
  │
  ▼
Repository layer
  │
  ▼
PostgreSQL / Supabase
  └── RLS + FORCE RLS
~~~

The browser never establishes tenant authority. Client-provided tenant or clinic identifiers are not trusted authorization primitives.

For AI execution:

~~~text
identity
→ authorization
→ capability/version
→ policy/risk
→ approval
→ provider/tool authorization
→ execution
→ output validation
→ side-effect authorization
→ audit/telemetry
~~~

AI output is untrusted data. AI cannot bypass tenant isolation or authorize its own consequential side effects.

## Features

| Capability | Description |
|---|---|
| Multi-tenancy | Organization-scoped healthcare operations with database-enforced isolation |
| AI workforce | Specialized administrative workers for reception, scheduling, intake, insurance, authorization, records, referrals, recall and communication |
| AI governance | Capability/version controls, policy/risk checks, approvals, tool authorization and output validation |
| Clinical documentation | Draft-oriented AI Scribe workflow with clinician review/edit/approval |
| Patient access | Administrative intake and access workflows |
| Insurance | Eligibility/authorization-oriented workforce boundaries |
| Revenue cycle | Claims/revenue-cycle operational workforce boundaries |
| Documents/referrals | Document, fax and referral intelligence |
| Command Center | Operational visibility across governed workforce activity |
| Interoperability | FHIR R4 and SMART App Launch boundaries |
| Reliability | Durable execution, recovery and disaster-recovery controls |
| Security | Secret/dependency scanning, SBOM, API security, AI security, RLS validation |
| Commercial | Subscription, entitlement, usage and quota controls |

## Enterprise engineering sequence

E1–E8 establish the foundation and production-proving baseline. E9–E24 define the enterprise sequence covering product architecture, patient access, insurance authorization, revenue cycle, patient financial workflows, documents/referrals, ambient clinical documentation, documentation intelligence, engagement/care gaps, unified workforce, Command Center, AI governance/MCP, interoperability productionization, enterprise security/compliance readiness, reliability/DR, and commercialization/GA.

The current phase status is governed by the forensic evidence ledger, not by phase labels or historical PR titles. See [docs/roadmap/enterprise-e9-e24.md](docs/roadmap/enterprise-e9-e24.md) and [docs/validation/p0-forensic-reconciliation.md](docs/validation/p0-forensic-reconciliation.md).

"Engineering verified" means the repository acceptance gates for the documented control passed. It does not mean that external providers, contracts, organizational safeguards, regulatory obligations, independent assurance, or production deployment requirements are complete.

## Documentation

- [Architecture](docs/architecture/)
- [AI governance](docs/ai/)
- [Security](docs/security/)
- [Reliability](docs/reliability/)
- [Interoperability](docs/interoperability/)
- [Commercial](docs/commercial/)
- [Operations](docs/operations/)
- [Roadmap](docs/roadmap/)
- [Validation evidence](docs/validation/)
- [Security policy](SECURITY.md)
- [Contribution guide](CONTRIBUTING.md)
- [Support](SUPPORT.md)
- [Changelog](CHANGELOG.md)
- [LLM index](llms.txt)

## Security

The canonical security chain is:

**tenant identity → authorization → domain service → repository → PostgreSQL/RLS**

Report vulnerabilities privately; do not publish exploit details, PHI, credentials or access tokens in public issues. See [SECURITY.md](SECURITY.md).

The dependency security gate also documents the temporary upstream-fork override required for the 2026 braces advisory. It is a release-gate remediation, not a reason to disable npm audit.

## Contributing

HEZQARA is proprietary software and accepts contributions only from authorized contributors. Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing code.

## License and acknowledgements

Copyright © 2024–2026 Tinlance Limited. All rights reserved.

HEZQARA is proprietary software. See [LICENSE](LICENSE).

HEZQARA uses third-party open-source dependencies subject to their respective licenses. Dependency security and license information is maintained through the repository lockfiles and CI controls.

<details>
<summary>Release and deployment notes</summary>

The repository currently has a v1.0.0 tag. Release notes are maintained in [CHANGELOG.md](CHANGELOG.md).

The frontend deployment target is Vercel. A Vercel deployment being READY is not, by itself, evidence of production readiness. The API, workers, Redis and PostgreSQL/Supabase require production-capable runtimes appropriate to the deployment topology.

See [docs/operations/e8-production-proving.md](docs/operations/e8-production-proving.md) and [docs/operations/vercel-deployment.md](docs/operations/vercel-deployment.md).

</details>

<details>
<summary>Support and troubleshooting</summary>

For software defects, use the repository Bug Report form. For feature proposals, use the Feature Request form. Security vulnerabilities must use private reporting.

When troubleshooting, record the exact commit, environment, command, relevant logs and whether the failure is in repository code or an external provider. Use synthetic data only.

</details>
