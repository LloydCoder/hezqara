# P0 — Forensic Reconciliation & Evidence Ledger

**Current baseline at reconciliation:** `b26f996d649adffc9d20d7cf6ade11efce0cae38`  
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

**Disposition:** code-side public route and fail-closed fallback hardening merged in PR #105 (`df8d218283f0a111ae34b30543a9c05a60da7943`) and was verified on the production Vercel deployment. Production authentication and backend connectivity remain an external configuration/release blocker until real values and live smoke evidence are available.

### P0-004 — Production configuration must not silently use localhost

A production Next.js build must not implicitly rewrite API calls to `http://localhost:8004`. Local development may retain that default; production without an API origin must fail clearly and must not pretend that backend requests are healthy.

**Disposition:** addressed by merged PR #105. CI and production build passed; deployed API requests now return an explicit 503 when the backend origin is absent instead of silently targeting localhost.

### P0-005 — Health, robots and sitemap public contract

Live inspection found `/health`, `/api/v1/health`, `/robots.txt` and `/sitemap.xml` returning HTTP 503 before route handling because the authentication proxy treated them as protected. The `/health` rewrite also conflated frontend liveness with backend health, and SEO metadata defaulted to localhost.

**Disposition:** addressed by merged PR #105 and verified on the production deployment: `/health`, `/robots.txt`, and `/sitemap.xml` return HTTP 200; `/api/health` reports `not_ready` with missing configuration; `/api/v1/health` returns `backend_not_configured` with HTTP 503. The 503 responses are expected while the real authentication and backend configuration are absent.

### P0-006 — Mobile navigation

The primary navigation is now available through a native popover-based mobile disclosure while preserving the desktop navigation. The menu exposes shared primary links and sign-in/get-started actions, supports keyboard activation and Escape dismissal, closes after route selection, and is covered at mobile and 320px viewport widths.

**Implementation:** [PR #107](https://github.com/LloydCoder/hezqara/pull/107), merged as `b26f996d649adffc9d20d7cf6ade11efce0cae38`.

**Verification:** CI, Security, E8 Production Proving, P0 Forensic Reconciliation, and Phases 9–16 Validation passed on the exact PR head; the same five workflows passed after merge on the canonical `main` revision.

**Disposition:** resolved as a repository-code blocker. This does not resolve the separate production authentication/backend configuration blocker recorded under P0-003.

### P0-007 — Dependency modernization

The reviewed backend and frontend dependency batches were consolidated to avoid overlapping lockfile/requirements changes and merged as PR #103 and PR #104 on 2026-10-15. Their resulting revision was `f5d2672864d3cb3d79aa293484f46e0ca764546b`; the later P0 deployment-contract PR #105 was merged as `df8d218283f0a111ae34b30543a9c05a60da7943`. CI, Security, E8 Production Proving, P0 Forensic Reconciliation, and Phases 9–16 Validation all passed on the current post-merge revision.

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


## Post-merge P0 deployment-contract verification — 2026-10-15

**Implementation PR:** [#105](https://github.com/LloydCoder/hezqara/pull/105)  
**Merged main revision:** `df8d218283f0a111ae34b30543a9c05a60da7943`

Production Vercel smoke checks against the deployment for this revision returned:

| Endpoint | Observed result | Interpretation |
|---|---|---|
| `/health` | HTTP 200 | Frontend liveness is public and independent of API configuration |
| `/robots.txt` | HTTP 200 | Public SEO endpoint; canonical sitemap URL is not localhost |
| `/sitemap.xml` | HTTP 200 | Public sitemap uses the production Vercel domain fallback |
| `/api/health` | HTTP 503, `not_ready` | Correctly reports missing authentication configuration and unreachable/unconfigured API |
| `/api/v1/health` | HTTP 503, `backend_not_configured` | Explicit fail-closed result; no implicit production localhost target |

The post-merge CI, Security, E8 Production Proving, P0 Forensic Reconciliation, and Phases 9–16 Validation workflows passed on the merged revision. The Vercel production deployment reached `READY`. The Vercel runtime-error query returned no grouped runtime errors in the preceding 24 hours.

## Current P0 disposition

- **Completed:** public health/SEO route handling, production-safe canonical URL fallback, no-localhost API fail-closed behavior, regression tests, and post-merge forensic verification.
- **Still blocked by external configuration:** no Vercel project environment variables were listed at inspection time. Real Clerk configuration and an actually deployed/reachable FastAPI origin must be supplied by the owner; credentials and endpoints must not be fabricated.
- **Still open in the repository:** accessible mobile navigation for the marketing header and its responsive regression tests.
- **Not established by these checks:** authenticated production workflows, tenant-isolation smoke tests against a live backend, worker health, provider integrations, backup/restore evidence, external assurance, or customer/pilot validation.

The P0 public-route and mobile-navigation repository-code subphases are complete. The broader P0 ledger remains open until the external production prerequisites are satisfied or explicitly dispositioned.


## Addendum — Post-merge mobile navigation audit (2026-10-15)

**Audited revision:** `b26f996d649adffc9d20d7cf6ade11efce0cae38`  
**Change:** [PR #107](https://github.com/LloydCoder/hezqara/pull/107)

- The change was reviewed and merged only after the exact PR head passed CI, Security, E8 Production Proving, P0 Forensic Reconciliation, and Phases 9–16 Validation.
- All five workflows also passed on the post-merge `main` revision.
- The implementation adds keyboard-operable mobile navigation, route-close behaviour, shared link definitions and Playwright checks for disclosure state, Escape/focus restoration, navigation close, desktop preservation and a 320px layout.
- The post-merge repository had zero open PRs and zero open non-PR issues at the time of this audit.
- Production authentication/backend configuration remains an external release blocker. No secrets or environment values were invented, committed or changed.

The audit connector could not currently read the Vercel project's environment inventory due to a permission-denied response. The previously recorded 2026-10-15 live inspection found no listed project environment variables; the owner must verify and configure the required production values before authenticated production smoke tests can pass.
