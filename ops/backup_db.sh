#!/usr/bin/env bash
# HEZQARA database backup helper.
# Requires DATABASE_URL. Optional BACKUP_DIR and BACKUP_RETENTION_DAYS.
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL must be set}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/hezqara}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
DATE="$(date -u '+%Y-%m-%d_%H%M%S')"
FILE="$BACKUP_DIR/hezqara_$DATE.sql.gz"

mkdir -p "$BACKUP_DIR"
umask 077

echo "HEZQARA backup started: $DATE UTC"
pg_dump "$DATABASE_URL"   --no-owner   --no-acl   --schema=public   | gzip -9 > "$FILE"

test -s "$FILE"
sha256sum "$FILE" > "$FILE.sha256"
find "$BACKUP_DIR" -name 'hezqara_*.sql.gz' -mtime +"$RETENTION_DAYS" -delete
find "$BACKUP_DIR" -name 'hezqara_*.sql.gz.sha256' -mtime +"$RETENTION_DAYS" -delete

echo "HEZQARA backup created: $FILE"
echo "Checksum: $FILE.sha256"
