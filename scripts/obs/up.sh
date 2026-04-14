#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
cd ops/observability

docker compose up -d --remove-orphans

echo ""
echo "✅ Observability stack is up"
echo "Grafana:     http://localhost:3000 (login: .env or GRAFANA_AUTH=user:pass)"
echo "Prometheus:  http://localhost:9090"
echo "Tempo:       http://localhost:3200"
echo "Loki:        http://localhost:3100"
echo "OTLP gRPC:   localhost:4317"
echo "OTLP HTTP:   http://localhost:4318"
echo ""
