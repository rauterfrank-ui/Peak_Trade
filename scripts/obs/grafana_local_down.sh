#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

COMPOSE_PROJECT="${GRAFANA_LOCAL_COMPOSE_PROJECT:-peaktrade-grafana-local}"

docker compose -p "$COMPOSE_PROJECT" \
  -f docs/webui/observability/DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml \
  -f docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml \
  down -v --remove-orphans || true

echo "Down."
