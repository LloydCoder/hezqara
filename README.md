# HEZQARA

> Documentation baseline: October 2026.

**Governed AI Workforce for Healthcare Operations**

HEZQARA is a multi-tenant healthcare operations platform for clinic front offices. It combines tenant-isolated healthcare workflows, governed AI execution, healthcare interoperability, durable background execution, commercial controls, and evidence-backed operational controls.

> **Engineering status:** E1–E8 and the post-E8 forensic hardening gate are verified on main by the repository automated validation suite. E9–E23 are implemented on main; E24 is the current implementation phase. This is an engineering verification statement—not a claim of HIPAA, GDPR, NDPA, SOC 2, ISO 27001, FHIR/SMART certification, clinical efficacy, customer ROI, SLA attainment, or arbitrary production-scale proof.

## Architecture at a glance

~~~text
Browser
  │
  ▼
Clerk identity / organization
  │
  ▼
Server authorization + immutable TenantContext
  │
  ▼
FastAPI domain/API layer
  │
  ├── AI governance → policy → approval → execution → validation → audit
  ├── Healthcare integrations → FHIR/SMART adapter boundaries
  ├── Durable workflows/jobs → PostgreSQL authority + Redis/Celery delivery
  └── Commercial controls → subscriptions → entitlements → usage/quota
  │
  ▼
Repository layer
  │
  ▼
PostgreSQL / Supabase
  │
  └── RLS + FORCE RLS + tenant-bound integrity
~~~

The browser never establishes tenant authority. Client-provided tenant/clinic identifiers are not trusted as authorization primitives. Database enforcement remains a defense-in-depth boundary.

## Verified engineering phases

| Phase | Scope | Status |
|---|---|---|
| E1 | AI governance enforcement | Verified |
| E2 | Canonical tenant security and data isolation | Verified |
| E3 | Durable execution and distributed reliability | Verified |
| E4 | Healthcare interoperability boundary | Verified |
| E5 | Enterprise security, privacy and compliance readiness | Verified |
| E6 | Commercial platform controls | Verified |
| E7 | First-clinic synthetic vertical slice | Verified |
| E8 | Production proving and operating maturity | Verified |
| Post-E8 | Forensic hardening of operational evidence and usage quotas | Verified |
| E9 | Product & Architecture Finalization | Verified |\n| E10 | Patient Access Workforce | Verified |\n| E11 | Insurance & Authorization Workforce | Verified |\n| E12 | Revenue Cycle Workforce | Verified |\n| E13 | Patient Financial Workforce | Verified |\n| E14 | Document, Fax & Referral Intelligence | Verified |\n| E15 | Ambient Clinical Documentation / AI Scribe | Verified |\n| E16 | Documentation Intelligence | Verified |\n| E17 | Patient Engagement & Care-Gap Workforce | Verified |\n| E18 | Unified Healthcare AI Workforce | Verified |\n| E19 | Hezqara Command Center | Verified |\n| E20 | AI Governance, MCP & Clinical Documentation Safety | Verified |\n| E21 | Interoperability & Provider Productionization | Verified |\n| E22 | Enterprise Security & Compliance Readiness | Verified |\n| E23 | Reliability, Scale & Disaster Recovery | Verified |\n| E24 | Commercialization, Independent Validation & GA | In progress |

See docs/roadmap/enterprise-e9-e24.md for the frozen E9–E24 enterprise sequence and docs/validation/e16-documentation-intelligence.md for the current E16 evidence ledger.

"Verified" means the repository acceptance gates for the documented control have passed. It does not mean the external deployment, providers, contracts, organizational safeguards, or regulatory obligations have been completed.

## Technology

- **Frontend:** Next.js 16, React 19, TypeScript
- **Authentication:** Clerk Organizations
- **Backend:** FastAPI, Python
- **Database:** PostgreSQL / Supabase with RLS and FORCE RLS
- **Durable execution:** PostgreSQL-backed state with Redis/Celery delivery and worker orchestration
- **Interoperability:** FHIR R4 (4.0.1) and SMART App Launch 2.2.0 boundaries
- **Commercial:** Stripe integration boundary
- **AI:** governed provider abstraction with deterministic validation, policy checks and human approval for consequential actions
- **Deployment:** Next.js frontend on Vercel; API/workers/database/Redis require production-capable runtime(s) appropriate to the deployment topology
- **CI/CD:** GitHub Actions with frontend, backend, database/RLS, E2E, Docker and security gates

## Repository layout

~~~text
.
├── backend/        # FastAPI application, domain services, workers and tests
├── frontend/       # Next.js application
├── supabase/       # PostgreSQL migrations and database security tests
├── docs/           # Architecture, security, operations and phase evidence
├── .github/        # CI and security workflows
├── vercel.json     # Vercel frontend project configuration
├── SECURITY.md     # Vulnerability reporting and security boundary
├── CONTRIBUTING.md # Contribution and verification workflow
└── LICENSE         # Repository license
~~~

## Local development

### Prerequisites

Use the versions declared by the repository/toolchain configuration. The frontend currently targets Node.js 24.x.

Typical services:

1. PostgreSQL/Supabase
2. Redis
3. FastAPI backend
4. Next.js frontend
5. Celery worker/beat when exercising durable background execution

### Frontend

~~~bash
cd frontend
npm ci
npm run lint
npm run type-check
npm run build
~~~

### Backend

Install the backend dependencies from the repository Python dependency configuration, then run the backend test suite. Database/RLS validation requires a migrated PostgreSQL test database.

### End-to-end

The CI workflow provisions the required test services and runs the Playwright suite against the application stack. Do not use production healthcare data in local, CI or preview environments.

## Configuration

Frontend configuration is documented in frontend/.env.example. Backend configuration is documented in backend/.env.example.

Never commit real credentials. NEXT_PUBLIC_* variables are browser-visible. Backend secrets—including database credentials, Clerk secret material, AI provider keys, Stripe secrets, webhook secrets and provider tokens—must remain server-side and be supplied by the deployment secret manager.

## Security model

The canonical security chain is:

**tenant identity → authorization → domain service → repository → PostgreSQL/RLS**

For AI:

**tenant identity → authorization → capability/version → policy/risk → approval → provider/tool authorization → execution → output validation → side-effect authorization → audit/telemetry**

AI output is untrusted data. AI is not an authorization authority and cannot bypass tenant isolation.

## Healthcare interoperability

HEZQARA uses FHIR R4 (4.0.1) as the explicit interoperability resource boundary and SMART App Launch 2.2.0 for the OAuth authorization contract. These are implementation boundaries, not certification claims. Provider-specific interoperability requires endpoint validation, credentials, contracts, implementation-guide testing and operational evidence.

## Production deployment

The frontend is the Vercel deployment target. The connected project uses frontend/ as its project root. The FastAPI API, Celery worker/beat, Redis and PostgreSQL/Supabase are not assumed to run inside the Next.js Vercel deployment.

Production release requirements are documented in docs/operations/e8-production-proving.md and docs/operations/vercel-deployment.md.

A Vercel deployment being READY is not, by itself, evidence of production readiness. Production deployment remains gated until E24 and the final forensic audit.

## Documentation map

- docs/architecture/ — canonical system and tenancy architecture
- docs/ai/ — AI governance and execution controls
- docs/security/ — security, privacy, incident response and forensic evidence
- docs/reliability/ — durable execution and recovery
- docs/interoperability/ — FHIR/SMART integration boundaries
- docs/commercial/ — subscriptions, billing and usage controls
- docs/operations/ — clinic activation, production proving and deployment
- docs/roadmap/ — enterprise phase sequence
- docs/validation/ — validation/acceptance evidence

## External standards and references

- OWASP ASVS 5.0.0
- OWASP API Security and GenAI/agentic security guidance
- NIST CSF 2.0
- NIST AI RMF 1.0 and NIST AI 600-1 (Generative AI Profile)
- NIST SP 800-218 SSDF 1.1
- NIST SP 800-61 Rev. 3
- HL7 FHIR R4 4.0.1
- HL7 SMART App Launch 2.2.0
- Applicable Da Vinci implementation guides
- Stripe API/webhook security guidance

Standards references guide engineering controls; they do not constitute certification.

## Security reporting

See SECURITY.md. Do not publish credentials, patient information, access tokens or exploitable details in public issues.

## License

Copyright © 2024–2026 Tinlance Limited.

HEZQARA is proprietary software. See LICENSE for the governing terms.
