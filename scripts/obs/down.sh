#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
cd ops/observability

docker compose down -v

echo "✅ Observability stack is down (volumes removed)"
