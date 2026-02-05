#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

unset GITHUB_TOKEN || true
trap 'if [ -t 0 ]; then stty echo; fi' EXIT

if [ -t 0 ]; then
  echo -n "Paste full ghp_/github_pat_ token (hidden): "
  stty -echo
  IFS= read -r GITHUB_TOKEN
  stty echo
  echo
else
  echo "NOTE: stdin is not a TTY; token input will be visible."
  printf "Paste full ghp_/github_pat_ token: "
  IFS= read -r GITHUB_TOKEN
fi
export GITHUB_TOKEN

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

echo
echo "Next: pick RUN_ID from above and run:"
echo "  bash scripts/ops/fetch_lint_gate_logs.sh <RUN_ID>"
