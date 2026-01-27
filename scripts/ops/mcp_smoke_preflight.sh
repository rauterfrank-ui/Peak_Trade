#!/usr/bin/env bash
set -euo pipefail

#
# scripts/ops/mcp_smoke_preflight.sh
#
# Purpose:
# - Operator-Preflight für MCP Tooling (Cursor): JSON-Parse + Help-Smokes (Playwright + Grafana)
# - Kein heredoc (vermeidet dquote>/heredoc>-Hänger beim Copy/Paste)
#
# Dependencies:
# - git (optional, für Repo-Root-Erkennung)
# - python3 (JSON parse)
# - npx (Playwright MCP help)
# - docker (Grafana MCP help)
#
# Exit codes:
# - 0: PASS
# - 2: Smoke/Config failure (JSON parse oder Help-Command fehlgeschlagen)
# - 3: Missing dependency (python3/npx/docker)
#
# Usage:
#   bash scripts/ops/mcp_smoke_preflight.sh
#   bash scripts/ops/mcp_smoke_preflight.sh --help
#

VERSION="0.1.0"

usage() {
  printf '%s\n' \
    "MCP Smoke Preflight (Cursor)" \
    "" \
    "Usage:" \
    "  bash scripts/ops/mcp_smoke_preflight.sh" \
    "  bash scripts/ops/mcp_smoke_preflight.sh --help" \
    "  bash scripts/ops/mcp_smoke_preflight.sh --version" \
    "" \
    "Exit codes:" \
    "  0  PASS" \
    "  2  Smoke/Config failure (JSON parse / help command failed)" \
    "  3  Missing dependency (python3/npx/docker)" \
    "" \
    "Notes:" \
    "  - Network may be used implicitly by: npx @playwright/mcp@latest --help, docker image pull." \
    "  - No heredocs are used for the JSON parse step."
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi
if [[ "${1:-}" == "--version" || "${1:-}" == "-V" ]]; then
  echo "$VERSION"
  exit 0
fi

echo "== PRE-FLIGHT (Ctrl-C falls du in > / dquote> / heredoc> haengst) =="

# 1) In Repo wechseln (falls Pfad abweicht: anpassen, aber nicht hart abbrechen)
REPO_DIR="${REPO_DIR:-$HOME/Peak_Trade}"
cd "$REPO_DIR" 2>/dev/null || cd "$(pwd)"

# 2) Verifizieren, dass wir im Repo sind
pwd
if command -v git >/dev/null 2>&1; then
  if repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    cd "$repo_root"
  fi
  git rev-parse --show-toplevel 2>/dev/null || true
  git status -sb 2>/dev/null || true
fi

echo
echo "== MCP SMOKE =="

need_cmd() {
  local c="$1"
  if ! command -v "$c" >/dev/null 2>&1; then
    echo "FAIL: required command not found: $c"
    exit 3
  fi
}

# JSON Parse Check (kein heredoc, um dquote>/heredoc>-Hänger zu vermeiden)
need_cmd python3
python3 -c 'import json,sys; p=".cursor/mcp.json"; json.load(open(p,"r",encoding="utf-8")); print(f"PASS: JSON parse {p}")' \
  || { echo "FAIL: JSON parse .cursor/mcp.json"; exit 2; }

# Playwright MCP Help
echo
echo "-- Playwright MCP (--help) --"
need_cmd npx
npx -y @playwright/mcp@latest --help >/dev/null 2>&1 \
  || { echo "FAIL: npx @playwright/mcp@latest --help"; exit 2; }
echo "PASS: npx @playwright/mcp@latest --help"

# Grafana MCP CLI Help (Docker)
echo
echo "-- Grafana MCP (-h) --"
need_cmd docker
docker run --rm grafana/mcp-grafana -h >/dev/null 2>&1 \
  || { echo "FAIL: docker run grafana/mcp-grafana -h"; exit 2; }
echo "PASS: docker run grafana/mcp-grafana -h"

echo
echo "OK: MCP smoke checks passed."
