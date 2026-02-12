#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

./scripts/ops/ensure_web_extra.sh

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
LOG_LEVEL="${LOG_LEVEL:-info}"
RELOAD="${RELOAD:-0}"

UV="${UV:-uv}"

if [[ "$RELOAD" == "1" ]]; then
  exec $UV run python -m uvicorn src.webui.app:app --reload --host "$HOST" --port "$PORT" --log-level "$LOG_LEVEL" "$@"
else
  exec $UV run python -m uvicorn src.webui.app:app --host "$HOST" --port "$PORT" --log-level "$LOG_LEVEL" "$@"
fi
