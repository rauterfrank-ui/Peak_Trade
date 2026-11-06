#!/usr/bin/env bash
# P85 — Live Data Ingest Readiness v1 (dry, no execution, no model calls)
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

MODE="${MODE:-shadow}"
OUT_DIR="${OUT_DIR:-}"
RUN_ID="${RUN_ID:-p85}"

if [[ -z "${OUT_DIR:-}" ]]; then
  echo "ERR: OUT_DIR required" >&2
  exit 2
fi

if [[ "$MODE" != "paper" && "$MODE" != "shadow" ]]; then
  echo "ERR: MODE must be paper|shadow" >&2
  exit 3
fi

mkdir -p "$OUT_DIR"

export MODE RUN_ID OUT_DIR
python3 -m src.ops.p85.run_live_data_ingest_readiness_v1 2>&1 | tee "$OUT_DIR/P85_RUN.log"
exit "${PIPESTATUS[0]}"
