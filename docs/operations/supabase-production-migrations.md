# Production database migration procedure

HEZQARA production Supabase project: `rqsmlpcifvznwtmktzxi` (us-east-1).

## Current recovery state

The production project was verified on 2026-11-07 as PostgreSQL 17.11 with no application tables, no application migration history table, no auth users, no Storage buckets, and no Storage objects. The repository contains 61 ordered SQL migrations. The repository's CI database-security job applies all 61 migrations to PostgreSQL 16 and runs the tenant-isolation/security SQL suites successfully.

## Required GitHub Actions secrets

Configure these repository secrets before running the workflow:

- `SUPABASE_ACCESS_TOKEN`: a Supabase personal access token with permission to manage migrations for this project.
- `SUPABASE_DB_PASSWORD`: the database password for the exact HEZQARA project above.

Never put either value in source control, workflow inputs, logs, or client-side environment variables.

## Two-stage deployment

1. Confirm the target project reference in this document and the Supabase dashboard.
2. Confirm the latest `HEZQARA CI`, `HEZQARA Security`, and `HEZQARA P0 Forensic Reconciliation` workflows are green on `main`.
3. Dispatch **HEZQARA Production Database Migrations** from the `main` branch using the default inputs (`dry_run_only=true`, `confirm_production=false`).
4. Review the complete migration plan in the run logs. The expected plan is the 61 repository migrations, in version order. Stop if the list differs.
5. Only after reviewing the dry-run output, dispatch the workflow again with `dry_run_only=false` and `confirm_production=true`.
6. The workflow serializes production migration runs and applies the checked-in migrations using `supabase db push`, which records repository migration versions in `supabase_migrations.schema_migrations`.
7. Confirm all 61 repository migrations appear as applied and rerun the Supabase security/performance/health advisors.

The workflow is deliberately manual. It does not run on pushes, pull requests, or deployments. It refuses to run from a non-main ref and fails closed if either secret is missing.

## Important constraints

- Do not use the Supabase MCP `apply_migration` tool to replay these existing files: it generates its own migration versions, which do not match the repository's three-digit migration prefixes and can create remote-only history entries.
- Do not use `supabase db reset --linked` against production. The remote reset command drops user-created database entities.
- Do not use `migration repair` to mark these migrations applied before their SQL has actually run.
- Do not proceed from dry run to apply until the operator has reviewed the plan.
- Keep application schema changes in version-controlled migrations after this recovery.
