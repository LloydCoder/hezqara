# P0 — Forensic Reconciliation & Evidence Ledger

**Current baseline at reconciliation:** `f5d2672864d3cb3d79aa293484f46e0ca764546b`  
**Repository:** `LloydCoder/hezqara`  
**Reconciliation date:** 2026-10-15

## Findings and current disposition

### P0-001 — Phase completion must be separated from production readiness

E1–E24 implementation and validation records exist in the repository. Code and CI cannot establish live provider contracts, production credentials, executed legal agreements, independent assurance, clinical/documentation efficacy, customer ROI or production-scale SLO attainment.

**Disposition:** distinction remains mandatory. External readiness is not inferred from CI.

### P0-002 — Canonical roadmap and evidence index

The canonical E9–E24 roadmap and validation index are present and covered by the P0 evidence-contract workflow.

**Disposition:** repository-documentation requirement implemented; phase evidence must continue to track the current commit.

### P0-003 — Vercel authentication and backend environment

A live Vercel inspection on 2026-10-15 found the `hezqara` project had no listed project environment variables. The homepage rendered, but protected and health/SEO routes returned HTTP 503 with the message that authentication was not configured. The project also has no verified custom production domain in the inspected domain listing.

Required values must be provided by the owner and stored in Vercel's environment configuration, not invented or committed:
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- `HEZQARA_API_INTERNAL_URL`
- `NEXT_PUBLIC_SITE_URL` (recommended canonical URL)

The API URL must identify an actually deployed, reachable backend service. The frontend Vercel project does not itself deploy FastAPI, PostgreSQL/Supabase, Redis or Celery workers.

**Disposition:** code-side public route and fail-closed fallback hardening is in progress in the P0 deployment-contract change. Production authentication and backend connectivity remain an external configuration/release blocker until real values and live smoke evidence are available.

### P0-004 — Production configuration must not silently use localhost

A production Next.js build must not implicitly rewrite API calls to `http://localhost:8004`. Local development may retain that default; production without an API origin must fail clearly and must not pretend that backend requests are healthy.

**Disposition:** addressed by the P0 deployment-contract change; verify via CI and deployed route checks before closure.

### P0-005 — Health, robots and sitemap public contract

Live inspection found `/health`, `/api/v1/health`, `/robots.txt` and `/sitemap.xml` returning HTTP 503 before route handling because the authentication proxy treated them as protected. The `/health` rewrite also conflated frontend liveness with backend health, and SEO metadata defaulted to localhost.

**Disposition:** addressed by the P0 deployment-contract change: expose public health/SEO paths, separate frontend health from API proxying, and use a production-safe canonical URL fallback. Verify deployed responses after merge.

### P0-006 — Mobile navigation

The current homepage markup exposes the primary navigation only at the large-screen breakpoint and does not provide an equivalent mobile menu in the inspected header.

**Disposition:** open. Implement an accessible mobile navigation and add interaction/responsive regression coverage in a separate serial change.

### P0-007 — Dependency modernization

The reviewed backend and frontend dependency batches were consolidated to avoid overlapping lockfile/requirements changes and merged as PR #103 and PR #104 on 2026-10-15. The resulting main revision is `f5d2672864d3cb3d79aa293484f46e0ca764546b`; the latest observed CI, Security, E8 Production Proving, P0 Forensic Reconciliation and Phases 9–16 Validation runs on that revision succeeded.

**Disposition:** merged and automated checks green on the stated revision. Reopen if later dependency or source changes invalidate the evidence.

## Required release gates

1. Required CI/security/E2E/database checks are green on the exact candidate commit.
2. Public health, robots and sitemap endpoints return their intended responses on the deployed frontend.
3. Clerk organization/tenant mapping is verified with real configured credentials.
4. The frontend reaches a real backend origin; no production localhost fallback is present.
5. Tenant-isolation checks and authenticated smoke tests pass against the deployed environment.
6. Worker liveness, durable-job health, backups/restores, provider connectivity, monitoring and rollback are evidenced.
7. External contracts, privacy obligations and independent assurance are handled before making corresponding public claims.
8. Mobile navigation work is completed and validated before marking P0 fully closed.

## Evidence rule

A phase is complete only when implementation, relevant automated verification, forensic review, documentation reconciliation and release evidence all agree on the same revision. Engineering CI is not regulatory certification or proof of production-scale operation.

## External reference alignment

The workflow uses least-privilege GitHub Actions permissions and pinned action SHAs. Healthcare assurance claims remain bounded to evidence. Applicable privacy, contractual and security obligations require separate assessment and cannot be self-certified by a repository test suite.
