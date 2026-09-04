#!/bin/bash
# Carenova AI — Supabase backup script
# Run via cron: 0 3 * * * /home/ubuntu/carenova/infrastructure/scripts/backup_db.sh

set -euo pipefail

BACKUP_DIR="/home/ubuntu/backups/carenova"
DATE=$(date '+%Y-%m-%d_%H%M')
R2_BUCKET="carenova-docs"

mkdir -p "$BACKUP_DIR"

echo "► Backup started: $DATE"

# Supabase exports via pg_dump (Supabase Frankfurt)
# Production: set DATABASE_URL in environment
if [ -z "${DATABASE_URL:-}" ]; then
    echo "⚠️  DATABASE_URL not set — skipping pg_dump"
else
    pg_dump "$DATABASE_URL" \
        --no-owner \
        --no-acl \
        --schema=public \
        -f "$BACKUP_DIR/carenova_$DATE.sql"

    gzip "$BACKUP_DIR/carenova_$DATE.sql"

    echo "✅ Backup created: carenova_$DATE.sql.gz"

    # Upload to Cloudflare R2
    # aws s3 cp "$BACKUP_DIR/carenova_$DATE.sql.gz" \
    #     "s3://$R2_BUCKET/backups/carenova_$DATE.sql.gz" \
    #     --endpoint-url "$R2_ENDPOINT"

    # Delete local backups older than 7 days
    find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete
    echo "✅ Old backups cleaned"
fi

echo "► Backup complete: $DATE"
