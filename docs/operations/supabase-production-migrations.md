# Production database migration procedure

HEZQARA production Supabase project: `rqsmlpcifvznwtmktzxi` (us-east-1).

## Current recovery state

The production project was verified on 2026-11-07 as PostgreSQL 17.11 with no application tables, no application migration history table, no auth users, no Storage buckets, and no Storage objects. The repository contains 61 ordered SQL migrations. The CI database-security job applies all 61 migrations to PostgreSQL 16 and runs the repository's tenant-isolation/security SQL suites successfully.

## Required GitHub Actions secrets

Configure these repository secrets before running the workflow:

- `SUPABASE_ACCESS_TOKEN`: a Supabase personal access token with permission to manage migrations for this project.
- `SUPABASE_DB_PASSWORD`: the database password for the exact HEZQARA project above.

Never put either value in source control, workflow inputs, logs, or client-side environment variables.

## Deployment

1. Confirm the target project reference in this document and the Supabase dashboard.
2. Confirm the latest `HEZQARA CI`, `HEZQARA Security`, and `HEZQARA P0 Forensic Reconciliation` workflows are green on `main`.
3. Run **HEZQARA Production Database Migrations** from GitHub Actions on the `main` branch.
4. Explicitly set `confirm_production=true`.
5. Review the printed migration list and dry-run output before the apply step.
6. The workflow serializes production migration runs and applies the checked-in migrations using `supabase db push`, which records the repository migration versions in `supabase_migrations.schema_migrations`.
7. Confirm all 61 repository migrations appear as applied and rerun the Supabase security/performance advisors.

The workflow is deliberately manual. It does not run on pushes, pull requests, or deployments. It refuses to run from a non-main ref and fails closed if either secret is missing.

## Important constraints

- Do not use the Supabase MCP `apply_migration` tool to replay these existing files: it generates its own migration versions, which do not match the repository's three-digit migration prefixes and can create remote-only history entries.
- Do not use `supabase db reset --linked` against production. The remote reset command drops user-created database entities.
- Do not use `migration repair` to mark these migrations applied before their SQL has actually run.
- If the dry run shows anything other than the expected 61 pending repository migrations, stop and investigate rather than applying.
- Keep application schema changes in version-controlled migrations after this recovery.
