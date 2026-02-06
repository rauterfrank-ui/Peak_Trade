#!/usr/bin/env bash
set -euo pipefail

# Restart helper for Prometheus instances expected on:
# - 9094:9090  (AI-Live Ops Prometheus)
# - 9095:9090  (Observability Prometheus)
#
# Auto-detects compose project names via `docker compose ls`.
# Optional overrides:
#   OBSE_PROJECT=...   AILIVE_PROJECT=...
# Optional compose args (if you start with -f files):
#   OBSE_COMPOSE='-f /path/to/compose.obse.yml'
#   AILIVE_COMPOSE='-f /path/to/compose.ai-live.yml'

need_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "missing: $1" >&2; exit 2; }; }
need_cmd docker

if ! command -v lsof >/dev/null 2>&1; then
  echo "[warn] lsof not found; port binding check will be skipped" >&2
fi

OBSE_COMPOSE="${OBSE_COMPOSE:-}"
AILIVE_COMPOSE="${AILIVE_COMPOSE:-}"

echo "== docker compose ls =="
docker compose ls || true

detect_project() {
  local needle="$1"
  local out=""
  out="$(docker compose ls --format json 2>/dev/null | python3 - <<PY 2>/dev/null || true
import json,sys
try:
  data=json.load(sys.stdin)
except Exception:
  data=[]
needle="${needle}"
hits=[]
for row in data:
  name=(row.get("Name") or "").strip()
  if needle in name:
    hits.append(name)
print(hits[0] if hits else "")
PY
)"
  echo "$out"
}

OBSE_PROJECT="${OBSE_PROJECT:-}"
AILIVE_PROJECT="${AILIVE_PROJECT:-}"

if [[ -z "${OBSE_PROJECT}" ]]; then
  OBSE_PROJECT="$(detect_project "observability")"
  [[ -z "${OBSE_PROJECT}" ]] && OBSE_PROJECT="$(detect_project "obse")"
  [[ -z "${OBSE_PROJECT}" ]] && OBSE_PROJECT="peaktrade-observability"
fi

if [[ -z "${AILIVE_PROJECT}" ]]; then
  AILIVE_PROJECT="$(detect_project "ai-live")"
  [[ -z "${AILIVE_PROJECT}" ]] && AILIVE_PROJECT="peaktrade-ai-live-ops"
fi

echo ""
echo "== detected projects =="
echo "OBSE_PROJECT=${OBSE_PROJECT} (expects host :9095 -> container :9090)"
echo "AILIVE_PROJECT=${AILIVE_PROJECT} (expects host :9094 -> container :9090)"
echo "OBSE_COMPOSE=${OBSE_COMPOSE:-<none>}"
echo "AILIVE_COMPOSE=${AILIVE_COMPOSE:-<none>}"

echo ""
echo "== status (before) =="
docker compose ${OBSE_COMPOSE} -p "${OBSE_PROJECT}" ps || true
docker compose ${AILIVE_COMPOSE} -p "${AILIVE_PROJECT}" ps || true

echo ""
echo "== soft restart (docker compose restart) =="
docker compose ${OBSE_COMPOSE} -p "${OBSE_PROJECT}" restart || true
docker compose ${AILIVE_COMPOSE} -p "${AILIVE_PROJECT}" restart || true

echo ""
echo "== status (after soft restart) =="
docker compose ${OBSE_COMPOSE} -p "${OBSE_PROJECT}" ps || true
docker compose ${AILIVE_COMPOSE} -p "${AILIVE_PROJECT}" ps || true

echo ""
echo "== readiness probes (after soft restart) =="
curl -fsS "http://localhost:9094/-/ready" && echo "9094 ready: OK" || echo "9094 ready: FAIL"
curl -fsS "http://localhost:9095/-/ready" && echo "9095 ready: OK" || echo "9095 ready: FAIL"

echo ""
echo "== hard restart (down/up, no -v) =="
docker compose ${OBSE_COMPOSE} -p "${OBSE_PROJECT}" down || true
docker compose ${AILIVE_COMPOSE} -p "${AILIVE_PROJECT}" down || true
docker compose ${OBSE_COMPOSE} -p "${OBSE_PROJECT}" up -d || true
docker compose ${AILIVE_COMPOSE} -p "${AILIVE_PROJECT}" up -d || true

echo ""
echo "== port binding check (lsof) =="
if command -v lsof >/dev/null 2>&1; then
  lsof -nP -iTCP:9094 -sTCP:LISTEN || true
  lsof -nP -iTCP:9095 -sTCP:LISTEN || true
fi

echo ""
echo "== readiness probes (after hard restart) =="
curl -fsS "http://localhost:9094/-/ready" && echo "9094 ready: OK" || echo "9094 ready: FAIL"
curl -fsS "http://localhost:9095/-/ready" && echo "9095 ready: OK" || echo "9095 ready: FAIL"

echo ""
echo "== logs (tail=200) if still failing =="
docker compose ${OBSE_COMPOSE} -p "${OBSE_PROJECT}" logs --tail=200 || true
docker compose ${AILIVE_COMPOSE} -p "${AILIVE_PROJECT}" logs --tail=200 || true
