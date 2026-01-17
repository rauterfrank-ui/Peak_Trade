#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

RUNTIME_DIR="scripts/obs/.runtime"
EXPORTER_PID_FILE="$RUNTIME_DIR/shadow_mvs_exporter.pid"
EXPORTER_LOG_FILE="$RUNTIME_DIR/shadow_mvs_exporter.log"
EXPORTER_HOST="${SHADOW_MVS_EXPORTER_HOST:-0.0.0.0}"
EXPORTER_PORT="${SHADOW_MVS_EXPORTER_PORT:-9109}"

mkdir -p "$RUNTIME_DIR"

if [[ -f "$EXPORTER_PID_FILE" ]]; then
  pid="$(cat "$EXPORTER_PID_FILE" || true)"
  if [[ -n "${pid:-}" ]] && kill -0 "$pid" >/dev/null 2>&1; then
    echo "==> Shadow MVS exporter already running (pid=$pid, port=$EXPORTER_PORT)"
  else
    rm -f "$EXPORTER_PID_FILE"
  fi
fi

if [[ ! -f "$EXPORTER_PID_FILE" ]]; then
  echo "==> Starting shadow MVS exporter (host=$EXPORTER_HOST port=$EXPORTER_PORT)"
  rm -f "$EXPORTER_LOG_FILE"
  python3 scripts/obs/mock_shadow_mvs_exporter.py \
    --host "$EXPORTER_HOST" \
    --port "$EXPORTER_PORT" \
    --mode shadow \
    --exchange sim \
    >"$EXPORTER_LOG_FILE" 2>&1 &
  echo $! >"$EXPORTER_PID_FILE"
  sleep 0.2
  pid="$(cat "$EXPORTER_PID_FILE" || true)"
  if [[ -n "${pid:-}" ]] && ! kill -0 "$pid" >/dev/null 2>&1; then
    echo "❌ Exporter failed to start. See log: $EXPORTER_LOG_FILE" >&2
    exit 1
  fi
fi

echo "==> Starting prometheus-local (:9092)"
docker compose -f docs/webui/observability/DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml up -d --force-recreate

echo "==> Starting grafana-only (:3000) with file provisioning"
docker compose -f docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml up -d --force-recreate

echo ""
echo "Up."
echo "- Grafana:     http://127.0.0.1:3000   (admin/admin)"
echo "- Prometheus:  http://127.0.0.1:9092"
echo "- Exporter:    http://127.0.0.1:${EXPORTER_PORT}/metrics"
echo ""
echo "Next:"
echo "  ./scripts/obs/shadow_mvs_local_verify.sh"
