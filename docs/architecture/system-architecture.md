# HEZQARA system architecture

HEZQARA is a multi-tenant healthcare operations and AI workforce platform.

Request flow: Clerk session → verified organization context → authorization → domain service → repository/integration adapter → PostgreSQL.

The FastAPI API is an HTTP adapter. Domain services own business rules. Repositories own persistence. External vendors are isolated behind integration adapters. AI agents use the workforce contract and approved tools; they do not access the database directly.

The Next.js App Router is the presentation layer. `frontend/src/app` owns routing; `frontend/src/features` owns domain UI and API-facing behavior.
