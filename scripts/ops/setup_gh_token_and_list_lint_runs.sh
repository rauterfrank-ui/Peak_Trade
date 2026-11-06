#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

trap 'if [ -t 0 ]; then stty echo; fi' EXIT

# Token aus Umgebung nutzen, wenn gesetzt (z. B. GITHUB_TOKEN=$(pbpaste) vorher)
if [ -n "${GITHUB_TOKEN:-}" ]; then
  echo "Using existing GITHUB_TOKEN from environment."
else
  if [ -t 0 ] && [ -n "${GITHUB_TOKEN_HIDDEN:-}" ]; then
    echo -n "Paste full ghp_/github_pat_ token (hidden): "
    stty -echo
    IFS= read -r GITHUB_TOKEN
    stty echo
    echo
  else
    printf "Paste full ghp_/github_pat_ token (visible): "
    IFS= read -r GITHUB_TOKEN
  fi
  # Führende/nachfolgende Leerzeichen und Zeilenumbrüche entfernen
  GITHUB_TOKEN="$(printf '%s' "$GITHUB_TOKEN" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr -d '\r\n')"
  export GITHUB_TOKEN
fi

python3 - <<'PY'
import os, re, sys
t=os.environ.get("GITHUB_TOKEN","")
print("len=", len(t), "prefix=", (t[:12]+"...") if t else "<empty>")
if not re.match(r"^(ghp_|github_pat_).{30,}$", t):
    print("ERROR: token not a full GitHub PAT (expected ghp_... or github_pat_..., long string).")
    sys.exit(1)
print("OK: token looks valid")
PY

curl -sS -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
  https://api.github.com/user | python3 -m json.tool | head -n 30

mkdir -p artifacts/gh_run_logs
export GITHUB_RUN_LOGS_DIR="$ROOT/artifacts/gh_run_logs"

bash scripts/ops/fetch_lint_gate_logs.sh

if [ -n "${1:-}" ]; then
  echo
  echo "Fetching logs for RUN_ID=$1 ..."
  bash scripts/ops/fetch_lint_gate_logs.sh "$1"
else
  echo
  echo "Next: pick RUN_ID from above and run:"
  echo "  bash scripts/ops/fetch_lint_gate_logs.sh <RUN_ID>"
  echo "  or: bash scripts/ops/setup_gh_token_and_list_lint_runs.sh <RUN_ID>"
fi
