#!/usr/bin/env bash
set -euo pipefail

# Bash 3.2 compatible: parallel arrays
PROM_NAMES=(shadow-mvs ai-live-ops observability)
PROM_CONTAINERS=(
  peaktrade-shadow-mvs-prometheus-local-1
  peaktrade-ai-live-ops-prometheus-local-1
  peaktrade-observability-prometheus-local-1
)

# Tuning knobs (override via env). BusyBox wget only supports -T (network read timeout).
: "${WGET_TIMEOUT_SECONDS:=5}"
: "${TMP_SUBDIR:=peaktrade_prom_targets_check}"

tmpdir="${TMPDIR:-/tmp}/${TMP_SUBDIR}"
mkdir -p "$tmpdir"

overall_bad=0

# Helper: check container running
is_running() {
  local c="$1"
  docker inspect -f '{{.State.Running}}' "$c" 2>/dev/null | grep -q '^true$'
}

for i in "${!PROM_NAMES[@]}"; do
  name="${PROM_NAMES[$i]}"
  c="${PROM_CONTAINERS[$i]}"
  out="$tmpdir/prom_targets_${name}.json"

  echo "== ${name} (${c}) =="

  if ! is_running "$c"; then
    echo "ERROR: container not running (or not found): $c"
    overall_bad=$((overall_bad+1))
    echo
    continue
  fi

  # Fetch targets API with timeout. BusyBox wget: only -T (network read timeout) is supported.
  if ! docker exec "$c" sh -lc \
    "wget -qO- -T ${WGET_TIMEOUT_SECONDS} http://127.0.0.1:9090/api/v1/targets" \
    > "$out"; then
    echo "ERROR: could not fetch targets API from container $c (wget failed)"
    overall_bad=$((overall_bad+1))
    echo
    continue
  fi

  python3 - <<PY
import json
p="$out"
d=json.load(open(p))
bad=[t for t in d.get("data",{}).get("activeTargets",[]) if t.get("lastError")]
print(f"bad_targets={len(bad)}")
if bad:
    for t in bad[:50]:
        job=t.get("labels",{}).get("job")
        url=t.get("scrapeUrl")
        err=t.get("lastError")
        print(f" - {job} | {url} | {err}")
PY

  # mark overall_bad if this instance has any bad targets
  if ! python3 - <<PY >/dev/null; then
import json
d=json.load(open("$out"))
bad=[t for t in d.get("data",{}).get("activeTargets",[]) if t.get("lastError")]
raise SystemExit(0 if len(bad)==0 else 1)
PY
    overall_bad=$((overall_bad+1))
  fi

  echo
done

if [[ "$overall_bad" -eq 0 ]]; then
  echo "OK: all Prometheus instances have bad_targets=0"
  exit 0
else
  echo "WARN: $overall_bad Prometheus instance(s) have errors"
  exit 2
fi
