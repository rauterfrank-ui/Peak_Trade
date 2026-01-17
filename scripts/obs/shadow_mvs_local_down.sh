#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

RUNTIME_DIR="scripts/obs/.runtime"
EXPORTER_PID_FILE="$RUNTIME_DIR/shadow_mvs_exporter.pid"

docker compose -f docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml down || true
docker compose -f docs/webui/observability/DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml down || true

if [[ -f "$EXPORTER_PID_FILE" ]]; then
  pid="$(cat "$EXPORTER_PID_FILE" || true)"
  if [[ -n "${pid:-}" ]] && kill -0 "$pid" >/dev/null 2>&1; then
    echo "==> Stopping shadow MVS exporter (pid=$pid)"
    kill "$pid" >/dev/null 2>&1 || true
    # allow graceful shutdown
    for _ in $(seq 1 20); do
      if ! kill -0 "$pid" >/dev/null 2>&1; then
        break
      fi
      sleep 0.1
    done
    if kill -0 "$pid" >/dev/null 2>&1; then
      echo "==> Exporter still running, sending SIGKILL"
      kill -9 "$pid" >/dev/null 2>&1 || true
    fi
  fi
  rm -f "$EXPORTER_PID_FILE"
fi

echo "Down."
