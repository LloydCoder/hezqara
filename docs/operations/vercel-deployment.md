# HEZQARA deployment topology

## Current repository boundary

HEZQARA is a monorepo with a Next.js frontend, FastAPI API, PostgreSQL/Supabase database, Redis/Celery workers and provider integrations. The repository CI proves these components independently and together; it does not create or configure a production cloud environment.

## Vercel

The Next.js application under `frontend/` is the Vercel deployment target. The connected Vercel project resolves the Next.js application as the frontend project root; the committed `vercel.json` pins the framework, locked npm install, build command and `.next` output used by that project. Keep the Vercel project connected to this repository so the committed deployment configuration remains versioned. Vercel should provide the frontend's public Clerk publishable key and server-side `HEZQARA_API_INTERNAL_URL` according to the selected deployment topology.

The FastAPI API, Celery worker/beat processes, Redis and PostgreSQL/Supabase are not assumed to run on Vercel. They require their own production-capable runtime and private connectivity appropriate to the deployment.

Do not put database credentials, Clerk secret keys, service-role credentials, AI provider keys, Stripe secrets or webhook signing secrets in `NEXT_PUBLIC_*` variables. Next.js public-prefixed variables are exposed to browser JavaScript.

## Environment separation

Use separate credentials and databases/projects for development, preview/staging and production. Never point a preview deployment at a production healthcare database. Production PHI must not be used for CI or preview validation.

## Required frontend variables

See `frontend/.env.example`.

- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`: public Clerk browser key.
- `NEXT_PUBLIC_API_URL`: optional browser API origin; leave empty to use the Next.js rewrite.
- `HEZQARA_API_INTERNAL_URL`: server-side Next.js rewrite target.

## Required backend variables

See `backend/.env.example`. Provider credentials are deployment secrets and must be supplied by the runtime secret manager.

## Release gate

A Vercel project is not considered production-ready merely because the Next.js build succeeds. Before production traffic, verify Clerk organization mapping, API authorization, tenant isolation, database backups/restore, worker liveness, provider contracts/credentials, monitoring, incident response and production smoke tests.
