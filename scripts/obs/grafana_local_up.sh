#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

COMPOSE_PROJECT="${GRAFANA_LOCAL_COMPOSE_PROJECT:-peaktrade-grafana-local}"

echo "==> Starting prometheus-local (:9092) + grafana-only (:3000) (compose project=$COMPOSE_PROJECT)"
docker compose -p "$COMPOSE_PROJECT" \
  -f docs/webui/observability/DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml \
  -f docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml \
  up -d --force-recreate --renew-anon-volumes --remove-orphans

echo ""
echo "Up."
echo "- Grafana:     http://127.0.0.1:3000   (admin/admin)"
echo "- Prometheus:  http://127.0.0.1:9092"
echo ""
echo "Next:"
echo "  ./scripts/obs/grafana_local_verify.sh"
