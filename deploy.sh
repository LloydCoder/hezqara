#!/bin/bash
# Carenova AI — Deploy Script
# Run on EC2: bash infrastructure/scripts/deploy.sh
# Called by GitHub Actions CI/CD on push to main

set -euo pipefail

REPO_DIR="/home/ubuntu/carenova"
COMPOSE_BASE="$REPO_DIR/infrastructure/docker/docker-compose.yml"
COMPOSE_PROD="$REPO_DIR/infrastructure/docker/docker-compose.prod.yml"

echo "══════════════════════════════════════"
echo "  Carenova AI — Deploy"
echo "  $(date '+%Y-%m-%d %H:%M:%S UTC')"
echo "══════════════════════════════════════"

cd "$REPO_DIR"

# Pull latest code
echo "► Pulling latest code..."
git fetch origin main
git reset --hard origin/main

# Build new images
echo "► Building images..."
docker compose \
    -f "$COMPOSE_BASE" \
    -f "$COMPOSE_PROD" \
    build --no-cache backend frontend

# Run database migrations
echo "► Running migrations (via Supabase)..."
echo "  Migrations applied via Supabase dashboard or supabase CLI"
echo "  Skipping auto-migrate in deploy script — manual step for safety"

# Restart services — zero downtime via Docker Compose
echo "► Restarting services..."
docker compose \
    -f "$COMPOSE_BASE" \
    -f "$COMPOSE_PROD" \
    up -d --remove-orphans

# Wait for health check
echo "► Waiting for health check..."
sleep 10
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8004/health)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Deploy successful — health check passed (HTTP $HTTP_CODE)"
else
    echo "❌ Health check failed (HTTP $HTTP_CODE)"
    echo "   Rolling back..."
    git reset --hard HEAD~1
    docker compose -f "$COMPOSE_BASE" -f "$COMPOSE_PROD" up -d
    exit 1
fi

# Cleanup old images
echo "► Cleaning up old images..."
docker image prune -f

echo ""
echo "══════════════════════════════════════"
echo "  Deploy complete."
echo "  Service: carenova.tinlance.com"
echo "  Port: 8004 (backend) | 3004 (frontend)"
echo "══════════════════════════════════════"
