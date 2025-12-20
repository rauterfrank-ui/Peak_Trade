#!/bin/bash
set -euo pipefail

# Peak_Trade – Phase 16L: Docker Wrapper for Stage1 Daily Snapshot
# Builds and runs the ops container to generate snapshot report

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$REPO_ROOT"

echo "==> Building peaktrade-ops image..."
docker compose -f docker-compose.obs.yml build

echo ""
echo "==> Running Stage1 Daily Snapshot in Docker..."
docker compose -f docker-compose.obs.yml run --rm peaktrade-ops stage1-snapshot "$@"

echo ""
echo "✅ Reports written to: $REPO_ROOT/reports/obs/stage1/"

