# Disaster Recovery & Restore

## Objectives

Every production deployment must define RPO and RTO by service/tenant class. E5 records measured restore-drill evidence; E8 will prove scale and operational maturity.

## Restore procedure

1. Identify the incident and freeze unsafe writes if required.
2. Select a known-good backup and record its immutable reference.
3. Restore into an isolated environment first.
4. Verify schema/migrations and application compatibility.
5. Validate tenant isolation and RLS.
6. Validate authentication and authorization.
7. Validate AI governance and approval state.
8. Validate integration metadata without exposing raw credentials.
9. Compare recovered data with expected integrity checks.
10. Record measured RPO/RTO and evidence.
11. Promote only after owner approval.

## Backup requirements

Backups must be encrypted, access-controlled, monitored and tested. Restore drills must be performed periodically and after material recovery architecture changes.

## Non-claims

A database schema that contains restore-drill fields is not proof that a cloud backup provider is configured or that a recovery target has been met.
