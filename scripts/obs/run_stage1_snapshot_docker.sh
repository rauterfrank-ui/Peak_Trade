#!/bin/bash
set -euo pipefail

# Peak_Trade – Phase 16L: Docker Wrapper for Stage1 Daily Snapshot
# Builds and runs the ops container to generate snapshot report

REPO_ROOT="$(git rev-parse --show-toplevel)"
COMPOSE_FILE="$REPO_ROOT/docker/docker-compose.obs.yml"

cd "$REPO_ROOT"

echo "==> Building peaktrade-ops image..."
docker compose -f "$COMPOSE_FILE" build

echo ""
echo "==> Running Stage1 Daily Snapshot in Docker..."
docker compose -f "$COMPOSE_FILE" run --rm peaktrade-ops stage1-snapshot "$@"

echo ""
echo "✅ Reports written to: $REPO_ROOT/reports/obs/stage1/"
