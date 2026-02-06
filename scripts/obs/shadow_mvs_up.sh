#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

PROJECT="${PROJECT:-peaktrade-shadow-mvs}"
ACTION="${1:-up}"   # up|restart|down|ps|logs

need_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "missing: $1" >&2; exit 2; }; }
need_cmd docker
need_cmd python3

# Resolve compose -f args: from docker compose ls ConfigFiles, or fallback to known files
cfg="$(docker compose ls --format json 2>/dev/null | PROJECT="$PROJECT" python3 -c '
import json, os, sys
proj = os.environ.get("PROJECT", "peaktrade-shadow-mvs").strip()
try:
    data = json.load(sys.stdin)
except Exception:
    data = []
out = []
for r in data:
    if (r.get("Name") or "").strip() == proj:
        cf = r.get("ConfigFiles") or r.get("ConfigFile")
        if isinstance(cf, list):
            out = [str(x).strip() for x in cf if str(x).strip()]
        elif isinstance(cf, str):
            out = [p.strip() for p in cf.split(",") if p.strip()]
        break
print(",".join(out))
' 2>/dev/null || true)"

args=()
if [[ -n "$cfg" ]]; then
  IFS=',' read -r -a files <<<"$cfg"
  for f in "${files[@]}"; do
    f="${f#"${f%%[![:space:]]*}"}"
    f="${f%"${f##*[![:space:]]}"}"
    [[ -n "$f" ]] && [[ -f "$f" ]] && args+=(-f "$f")
  done
fi
if [[ ${#args[@]} -eq 0 ]]; then
  base="docs/webui/observability/DOCKER_COMPOSE_PROMETHEUS_LOCAL.yml"
  graf="docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml"
  [[ -f "$base" ]] && args+=(-f "$base")
  [[ -f "$graf" ]] && args+=(-f "$graf")
fi

echo "PROJECT=$PROJECT"
echo "COMPOSE_ARGS=${args[*]:-<none>}"
echo "ACTION=$ACTION"

if [[ ${#args[@]} -eq 0 ]]; then
  echo "No compose files found." >&2
  exit 2
fi

case "$ACTION" in
  up)
    docker compose "${args[@]}" -p "$PROJECT" up -d
    ;;
  restart)
    docker compose "${args[@]}" -p "$PROJECT" restart
    ;;
  down)
    docker compose "${args[@]}" -p "$PROJECT" down
    ;;
  ps)
    docker compose "${args[@]}" -p "$PROJECT" ps
    ;;
  logs)
    docker compose "${args[@]}" -p "$PROJECT" logs --tail=200
    ;;
  *)
    echo "usage: $0 [up|restart|down|ps|logs]" >&2
    exit 2
    ;;
esac
