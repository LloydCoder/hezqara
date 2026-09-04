# HEZQARA

**AI Workforce for Healthcare**

Hezqara automates routine healthcare front-office and administrative workflows across calls, scheduling, intake, insurance, prior authorization, refills, records, referrals, recall, and email—while keeping sensitive actions behind explicit authorization, audit, and human-review controls.

> **Product status:** engineering hardening in progress. This repository is not yet a production-compliance certification.

## Core workforce

| Agent | Responsibility |
|---|---|
| **Reception** | Inbound patient communication, intent detection, and routing |
| **Scheduling** | Availability lookup, appointment workflows, and EHR write-back |
| **Intake** | Demographics, insurance, and pre-visit information collection |
| **Insurance** | Eligibility and benefits workflow support |
| **Prior Authorization** | Authorization workflow preparation, submission, and status tracking |
| **Refill** | Medication-request intake and routing for authorized workflows |
| **Records** | Identity verification and medical-record request workflows |
| **Referrals** | Specialist referral creation and status tracking |
| **Recall** | Patient outreach campaigns across supported channels |
| **Email** | Inbox triage, drafting, and appointment communications |

## Platform capabilities

- AI front-office automation
- Scheduling and patient engagement
- Insurance and revenue-cycle workflow support
- Prior-authorization and referral operations
- Voice and WhatsApp communication adapters
- EHR integration layer with FHIR-oriented interfaces
- Tenant isolation and role-based access controls
- Audit logging and security controls
- Analytics and operational visibility
- Standalone workflows for environments without an EHR

## Architecture direction

The target architecture is a modular monolith with clear boundaries between:

- domain logic
- workflow orchestration
- AI/model routing
- healthcare integrations
- tenant/security enforcement
- data access
- observability and evaluation

AI agents must not bypass workflow authorization or directly perform unrestricted database mutations. External side effects should pass tenant, authorization, safety, and audit controls.

## Technology

| Layer | Technology |
|---|---|
| API | FastAPI + Python 3.12 |
| Web | Next.js + React + TypeScript |
| Database | PostgreSQL / Supabase |
| Authentication | Clerk |
| Voice | Retell AI adapter |
| Messaging | WhatsApp adapter |
| AI | Policy-based model routing |
| Memory | Graphiti / FalkorDB adapter |
| Tasks | Celery + Redis |
| Storage | S3-compatible object storage |
| Deployment | Docker + AWS |
| CI/CD | GitHub Actions |

## Security and healthcare boundary

Hezqara is designed for healthcare workloads, but software code alone does not establish HIPAA compliance, GDPR compliance, or any other regulatory certification. Production deployment requires documented risk analysis, appropriate contracts/BAAs where applicable, least-privilege configuration, vendor due diligence, incident response, retention/deletion controls, access reviews, and operational safeguards.

The product should remain focused on administrative and workflow automation. High-risk clinical decisions, diagnosis, prescribing, emergency triage, and other regulated clinical functions require explicit product-specific regulatory analysis and appropriate clinician oversight.

## Development

The repository is currently being consolidated from an earlier multi-layout build. Before a production release, the following gates must pass:

1. One canonical application layout.
2. No generated caches or compiled artifacts committed.
3. Reproducible dependency installation with lockfiles where appropriate.
4. Backend imports and startup verified from a clean checkout.
5. Frontend type-check, lint, and production build verified.
6. Docker images build from clean contexts.
7. Database migrations execute in order against a clean database.
8. Tenant isolation/RLS tests pass.
9. Security and secret-scanning checks pass.
10. AI safety, prompt-injection, tool-authorization, and data-egress evaluations pass.
11. End-to-end critical workflows pass in a production-like environment.
12. Only then should external customer outreach represent the platform as production-ready.

## Repository hygiene

Generated Python bytecode, pytest caches, Node build output, local environments, logs, and local secrets are excluded by `.gitignore`. Existing historical generated artifacts still need to be removed from Git history/tree as part of the repository consolidation.

## License

Proprietary — Tinlance Limited. All rights reserved.
