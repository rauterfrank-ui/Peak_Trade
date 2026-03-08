#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

echo "ERROR: scripts/obs/up.sh is intentionally disabled."
echo "Reason: legacy path ops/observability/ does not exist in this repository."
echo "Safe-next-step: inspect docker/docker-compose.obs.yml and docs/webui/observability before introducing a new start path."
exit 1
