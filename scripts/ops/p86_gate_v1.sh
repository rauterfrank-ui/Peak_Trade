#!/usr/bin/env bash
set -euo pipefail

# Exit codes: 0 READY, 2 usage, 3 gate failed, 4 internal error

MODE="${MODE:-shadow}"
RUN_ID="${RUN_ID:-p86_$(date -u +%Y%m%dT%H%M%SZ)}"
OUT_DIR="${OUT_DIR:-out/ops/p86_gate_${RUN_ID}}"

case "${MODE}" in
  paper|shadow) ;;
  *) echo "P86_FAIL mode_not_allowed: ${MODE}" >&2; exit 3 ;;
esac

mkdir -p "${OUT_DIR}"

python3 - <<PY || exit 4
from pathlib import Path
import json
from src.ops.p86 import run_online_readiness_plus_ingest_gate_v1, P86RunContextV1

ctx = P86RunContextV1(
  mode="${MODE}",
  run_id="${RUN_ID}",
  out_dir=Path("${OUT_DIR}"),
)
out = run_online_readiness_plus_ingest_gate_v1(ctx)
Path("${OUT_DIR}").joinpath("P86_GATE_RESULT.json").write_text(json.dumps(out, indent=2, sort_keys=True))
print("P86_GATE_OK" if out.get("overall_ok") else "P86_GATE_FAIL", "overall_ok=", out.get("overall_ok"), "out_dir=", "${OUT_DIR}")
PY

if python3 - <<PY
import json, pathlib, sys
p = pathlib.Path("${OUT_DIR}")/"P86_GATE_RESULT.json"
o = json.loads(p.read_text())
sys.exit(0 if o.get("overall_ok") else 1)
PY
then
  exit 0
else
  exit 3
fi
