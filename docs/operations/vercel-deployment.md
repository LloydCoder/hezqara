# HEZQARA Deployment Topology

## Repository boundary

HEZQARA is a monorepo containing a Next.js frontend, FastAPI API, PostgreSQL/Supabase database, Redis/Celery worker and beat processes, and external provider integrations.

Repository CI proves these components and their integration tests. It does not create or configure a production cloud environment.

## Vercel frontend

The Next.js application under frontend/ is the Vercel deployment target. The connected Vercel project uses frontend/ as its project root.

The committed vercel.json keeps the frontend build/install behavior versioned. Keep the Vercel project's Root Directory aligned with frontend/.

Vercel should provide:

- NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
- HEZQARA_API_INTERNAL_URL;
- optionally NEXT_PUBLIC_API_URL when the browser must call an external API origin directly.

Do not put database credentials, Clerk secret keys, AI provider keys, Stripe secrets, webhook signing secrets or provider tokens in NEXT_PUBLIC_* variables.

## Backend and workers

The FastAPI API, Celery worker/beat, Redis and PostgreSQL/Supabase are not assumed to run inside the Next.js Vercel project. They require a production-capable runtime with private connectivity and appropriate operational controls.

Backend environment variables are documented in backend/.env.example.

## Environment separation

Use separate credentials and databases/projects for local development, preview/staging and production.

Never point a preview deployment at a production healthcare database. Never introduce production PHI into CI, preview, benchmarks or test fixtures.

## Release gate

A Vercel build succeeding is only a build signal. Production release additionally requires:

1. all required CI/security/E2E checks green;
2. database migration validation;
3. authenticated smoke validation against the deployed artifact;
4. Clerk organization/tenant mapping verified;
5. tenant-isolation verification;
6. backup/restore evidence;
7. worker liveness and durable-job health;
8. provider contracts/credentials verified;
9. monitoring and incident response ready;
10. rollback path tested;
11. no unresolved release-blocking incident.

If Vercel Deployment Protection is enabled, unauthenticated external HTTP checks may return a protection response even when the deployment is healthy. Use an authenticated smoke path for protected deployments.

## References

- Vercel monorepo deployment guidance: https://vercel.com/academy/production-monorepos/deploy-web-app
- Next.js documentation: https://nextjs.org/docs
