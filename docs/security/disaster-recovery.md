# Disaster Recovery & Restore

## Objectives

Every production deployment must define RPO and RTO by service/tenant class. E5 established restore-drill evidence and E8 added the final operational evidence layer for recovery drills, worker liveness, SLOs, incidents and changes.

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
10. Record measured RPO/RTO and recovery-drill evidence.
11. Promote only after owner approval.

## Backup requirements

Backups must be encrypted, access-controlled, monitored and tested. `ops/backup_db.sh` requires `DATABASE_URL`, creates a compressed public-schema dump, records a SHA-256 checksum and applies configurable local retention. A successful script run is not proof that an external backup store, encryption-at-rest policy or cloud restore target is configured.

Restore drills must be performed periodically and after material recovery architecture changes.

## E8 operational evidence

The `recovery_drills` table records drill type, start/completion, result, measured RPO/RTO, owner and evidence. A drill is not passed merely because a row exists; the evidence must demonstrate an actual recovery test.

## Non-claims

The repository does not claim a specific cloud backup provider, RPO/RTO target, regulatory recovery certification or production disaster-recovery SLA without deployment evidence.
