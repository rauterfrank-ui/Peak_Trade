#!/usr/bin/env bash
set -euo pipefail

# P79 — Supervisor Health Gate v1 (paper/shadow only)
#
# Exit codes:
#   0 = OK
#   2 = usage / config error
#   3 = gate failed
#
# Env:
#   MODE                (required) paper|shadow
#   OUT_DIR             (required) supervisor output dir (contains tick_*/)
#   PIDFILE             (optional) pidfile path to validate (must be live if present)
#   MAX_AGE_SEC         (optional) max allowed age for newest tick dir (default 300)
#   REQUIRE_P76_FILES   (optional) 1 to require P76 artifacts per tick (default 1)
#
# Evidence:
#   Writes to OUT_DIR/p79_health_gate_v1.json (json) and prints P79_GATE_OK / P79_GATE_FAIL

die_usage() { echo "P79_USAGE: $*" >&2; exit 2; }
fail_gate()  { echo "P79_GATE_FAIL: $*" >&2; exit 3; }

MODE="${MODE:-}"
OUT_DIR="${OUT_DIR:-}"
PIDFILE="${PIDFILE:-}"
MAX_AGE_SEC="${MAX_AGE_SEC:-300}"
REQUIRE_P76_FILES="${REQUIRE_P76_FILES:-1}"

[ -n "${MODE}" ] || die_usage "MODE required (paper|shadow)"
[ "${MODE}" = "paper" ] || [ "${MODE}" = "shadow" ] || fail_gate "mode_not_allowed: ${MODE} (paper|shadow only)"
[ -n "${OUT_DIR}" ] || die_usage "OUT_DIR required"
[ -d "${OUT_DIR}" ] || fail_gate "out_dir_missing: ${OUT_DIR}"

# pidfile validation (if provided + exists)
pid_ok=true
pid_val=""
if [ -n "${PIDFILE}" ] && [ -e "${PIDFILE}" ]; then
  pid_val="$(cat "${PIDFILE}" 2>/dev/null || true)"
  if [ -z "${pid_val}" ]; then
    pid_ok=false
  else
    if kill -0 "${pid_val}" 2>/dev/null; then
      pid_ok=true
    else
      pid_ok=false
    fi
  fi
fi

# newest tick dir (macOS stat -f %m; Linux stat -c %Y)
stat_mtime() {
  if stat -f %m "$1" 2>/dev/null; then
    return 0
  fi
  stat -c %Y "$1" 2>/dev/null || echo 0
}

newest_tick=""
newest_mtime=0
while IFS= read -r d; do
  [ -d "$d" ] || continue
  mt="$(stat_mtime "$d")"
  if [ "${mt}" -gt "${newest_mtime}" ]; then
    newest_mtime="${mt}"
    newest_tick="$d"
  fi
done < <(find "${OUT_DIR}" -maxdepth 1 -type d -name 'tick_*' 2>/dev/null | LC_ALL=C sort)

[ -n "${newest_tick}" ] || fail_gate "no_ticks_found (expected tick_* dirs in OUT_DIR)"

now="$(date +%s)"
age=$(( now - newest_mtime ))
[ "${age}" -le "${MAX_AGE_SEC}" ] || fail_gate "ticks_stale age_sec=${age} max_age_sec=${MAX_AGE_SEC} newest=${newest_tick}"

# per-tick required artifacts (if enabled)
# P76 writes: P76_RESULT.txt, ONLINE_READINESS_ENV.json, P71_GATE.log, P72_PACK.log
missing_files=0
if [ "${REQUIRE_P76_FILES}" = "1" ]; then
  while IFS= read -r d; do
    [ -d "$d" ] || continue
    ok=false
    [ -f "$d/P76_RESULT.txt" ] && ok=true
    [ -f "$d/ONLINE_READINESS_ENV.json" ] && ok=true
    [ -f "$d/P71_GATE.log" ] && ok=true
    [ -f "$d/P72_PACK.log" ] && ok=true
    [ -f "$d/readiness_report.json" ] && ok=true
    [ -f "$d/manifest.json" ] && ok=true
    if [ "$ok" = false ]; then
      missing_files=$((missing_files+1))
    fi
  done < <(find "${OUT_DIR}" -maxdepth 1 -type d -name 'tick_*' 2>/dev/null | LC_ALL=C sort)
fi

[ "${pid_ok}" = true ] || fail_gate "pidfile_stale pid=${pid_val:-} pidfile=${PIDFILE}"
[ "${missing_files}" -eq 0 ] || fail_gate "missing_tick_artifacts ticks_missing=${missing_files}"

# write evidence json
EVI_JSON="${OUT_DIR}/p79_health_gate_v1.json"
python3 - "${EVI_JSON}" "${MODE}" "${OUT_DIR}" "${PIDFILE}" "${pid_val}" "${MAX_AGE_SEC}" "${age}" "${newest_tick}" "${missing_files}" <<'PY'
import json
import sys
import os
import time

path, mode, out_dir, pidfile, pid, max_age, age, newest, miss = sys.argv[1:10]
doc = {
    "version": "p79_health_gate_v1",
    "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "mode": mode,
    "out_dir": out_dir,
    "pidfile": pidfile if pidfile else None,
    "pid": int(pid) if pid and pid.isdigit() else (pid if pid else None),
    "max_age_sec": int(max_age),
    "newest_tick": newest,
    "newest_tick_age_sec": int(age),
    "missing_tick_artifacts": int(miss),
    "overall_ok": True,
}
parent = os.path.dirname(path)
if parent:
    os.makedirs(parent, exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
    json.dump(doc, f, indent=2, sort_keys=True)
PY

echo "P79_GATE_OK out_dir=${OUT_DIR} newest_tick=$(basename "${newest_tick}") age_sec=${age}"
exit 0
