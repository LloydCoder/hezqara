#!/usr/bin/env bash
# HEZQARA AI deployment helper.
set -euo pipefail

REPO_DIR="${HEZQARA_REPO_DIR:-/opt/hezqara}"
cd "$REPO_DIR"

echo "HEZQARA deploy: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
git fetch origin main
git reset --hard origin/main

docker compose build backend frontend
docker compose up -d --remove-orphans

for _ in {1..30}; do
  if curl -fsS http://localhost:8004/health >/dev/null; then
    echo "HEZQARA backend healthy"
    exit 0
  fi
  sleep 2
done

echo "HEZQARA backend failed health check" >&2
docker compose ps
docker compose logs --tail=100 backend
exit 1
