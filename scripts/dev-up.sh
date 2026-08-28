#!/usr/bin/env bash
set -euo pipefail

# Boot docker services for local dev
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

# Create docker/.env from example if missing
if [ ! -f docker/.env ]; then
  echo "==> Creating docker/.env from template"
  cp docker/.env.example docker/.env
fi

echo "==> Booting postgres + qdrant"
cd docker
docker compose up -d

echo "==> Waiting for services to be healthy..."
for i in {1..30}; do
  PG_OK=$(docker compose ps postgres --format json 2>/dev/null | grep -c '"Health":"healthy"' || true)
  QD_OK=$(docker compose ps qdrant --format json 2>/dev/null | grep -c '"Health":"healthy"' || true)
  if [ "$PG_OK" -ge 1 ] && [ "$QD_OK" -ge 1 ]; then
    echo "==> Both services healthy"
    exit 0
  fi
  sleep 1
done

echo "!! Services did not become healthy in 30s"
docker compose ps
exit 1
