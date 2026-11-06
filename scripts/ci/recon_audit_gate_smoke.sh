#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

WRAPPER="scripts/execution/recon_audit_gate.sh"
if [[ ! -f "$WRAPPER" ]]; then
  echo "ERROR: wrapper not found: $WRAPPER" >&2
  exit 1
fi

run_and_capture() {
  local mode="$1"
  local out err rc
  out="$(mktemp)"
  err="$(mktemp)"
  set +e
  bash "$WRAPPER" "$mode" >"$out" 2>"$err"
  rc=$?
  set -e
  echo "$out|$err|$rc"
}

# 1) summary-text
IFS="|" read -r OUT ERR RC < <(run_and_capture "summary-text")
if [[ "$RC" -ne 0 ]]; then
  echo "ERROR: summary-text exit=$RC" >&2
  echo "--- stderr ---" >&2; tail -n 200 "$ERR" >&2 || true
  echo "--- stdout ---" >&2; tail -n 200 "$OUT" >&2 || true
  exit 1
fi
if [[ ! -s "$OUT" ]]; then
  echo "ERROR: summary-text produced empty stdout" >&2
  exit 1
fi

# 2) summary-json (validate JSON)
IFS="|" read -r OUT ERR RC < <(run_and_capture "summary-json")
if [[ "$RC" -ne 0 ]]; then
  echo "ERROR: summary-json exit=$RC" >&2
  echo "--- stderr ---" >&2; tail -n 200 "$ERR" >&2 || true
  echo "--- stdout ---" >&2; tail -n 200 "$OUT" >&2 || true
  exit 1
fi
python3 - "$OUT" <<'PY'
import json, sys, pathlib
p = pathlib.Path(sys.argv[1])
s = p.read_text(encoding="utf-8", errors="replace")
json.loads(s)
PY

# 3) gate (accept 0 or 2)
IFS="|" read -r OUT ERR RC < <(run_and_capture "gate")
if [[ "$RC" -ne 0 && "$RC" -ne 2 ]]; then
  echo "ERROR: gate exit=$RC (expected 0 or 2)" >&2
  echo "--- stderr ---" >&2; tail -n 200 "$ERR" >&2 || true
  echo "--- stdout ---" >&2; tail -n 200 "$OUT" >&2 || true
  exit 1
fi

echo "OK: recon_audit_gate wrapper smoke passed (gate exit=$RC)"
