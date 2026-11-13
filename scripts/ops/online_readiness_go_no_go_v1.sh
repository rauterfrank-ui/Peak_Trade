#!/usr/bin/env bash
set -euo pipefail

output_dir="${OUT_DIR_OVERRIDE:-${OUT_DIR:-}}"
run_id="${RUN_ID_OVERRIDE:-${RUN_ID:-}}"

[ -n "$output_dir" ] || { echo "ERR: OUT_DIR (or OUT_DIR_OVERRIDE) required" >&2; exit 2; }
[ -n "$run_id" ] || { echo "ERR: RUN_ID (or RUN_ID_OVERRIDE) required" >&2; exit 2; }

mkdir -p "$output_dir"
echo "P76_NOT_READY reason=retired_readiness_chain dependencies=P71,P72" \
  | tee "$output_dir/P76_RESULT.txt"
exit 3
