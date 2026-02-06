#!/usr/bin/env bash
set -euo pipefail

# Diagnose + Start for Prometheus instances expected on:
# - 9094:9090  (AI-Live Ops Prometheus)
# - 9095:9090  (Observability Prometheus)
#
# Uses `docker compose ls` to auto-detect project names.
# Optional overrides:
#   OBSE_PROJECT=...   AILIVE_PROJECT=...
# Optional compose args (if you start with -f files):
#   OBSE_COMPOSE='-f /path/to/compose.obse.yml'
#   AILIVE_COMPOSE='-f /path/to/compose.ai-live.yml'
#
# Fallback projects:
#   peaktrade-observability, peaktrade-ai-live-ops

need_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "missing: $1" >&2; exit 2; }; }
need_cmd docker

# macOS lsof is expected; if not available, we still proceed with curl + docker ps
if ! command -v lsof >/dev/null 2>&1; then
  echo "[warn] lsof not found; port binding check will be skipped" >&2
fi

OBSE_COMPOSE="${OBSE_COMPOSE:-}"
AILIVE_COMPOSE="${AILIVE_COMPOSE:-}"

echo "== docker compose ls =="
docker compose ls || true

RESOLVE_JSON="$(python3 scripts/obs/resolve_obse_ailive_compose.py)"
OBSE_PROJECT="$(printf '%s' "$RESOLVE_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("OBSE_PROJECT",""))')"
AILIVE_PROJECT="$(printf '%s' "$RESOLVE_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("AILIVE_PROJECT",""))')"
OBSE_COMPOSE_ARGS="$(printf '%s' "$RESOLVE_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("OBSE_COMPOSE_ARGS",""))')"
AILIVE_COMPOSE_ARGS="$(printf '%s' "$RESOLVE_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("AILIVE_COMPOSE_ARGS",""))')"

echo ""
echo "== resolved config =="
echo "OBSE_PROJECT=${OBSE_PROJECT} (expects host :9095 -> container :9090)"
echo "AILIVE_PROJECT=${AILIVE_PROJECT} (expects host :9094 -> container :9090)"
echo "OBSE_COMPOSE_ARGS=${OBSE_COMPOSE_ARGS:-<none>}"
echo "AILIVE_COMPOSE_ARGS=${AILIVE_COMPOSE_ARGS:-<none>}"

echo ""
echo "== status (ps) =="
eval "docker compose ${OBSE_COMPOSE_ARGS:-} -p \"${OBSE_PROJECT}\" ps" || true
eval "docker compose ${AILIVE_COMPOSE_ARGS:-} -p \"${AILIVE_PROJECT}\" ps" || true

echo ""
echo "== logs (tail=200) =="
eval "docker compose ${OBSE_COMPOSE_ARGS:-} -p \"${OBSE_PROJECT}\" logs --tail=200" || true
eval "docker compose ${AILIVE_COMPOSE_ARGS:-} -p \"${AILIVE_PROJECT}\" logs --tail=200" || true

echo ""
echo "== start (up -d) =="
eval "docker compose ${OBSE_COMPOSE_ARGS:-} -p \"${OBSE_PROJECT}\" up -d" || true
eval "docker compose ${AILIVE_COMPOSE_ARGS:-} -p \"${AILIVE_PROJECT}\" up -d" || true

echo ""
echo "== port binding check (lsof) =="
if command -v lsof >/dev/null 2>&1; then
  lsof -nP -iTCP:9094 -sTCP:LISTEN || true
  lsof -nP -iTCP:9095 -sTCP:LISTEN || true
fi

echo ""
echo "== prom containers overview (docker ps) =="
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep -n -E 'prometheus|9094|9095' || true

echo ""
echo "== readiness probes =="
curl -fsS "http://localhost:9094/-/ready" && echo "9094 ready: OK" || echo "9094 ready: FAIL"
curl -fsS "http://localhost:9095/-/ready" && echo "9095 ready: OK" || echo "9095 ready: FAIL"
