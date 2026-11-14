#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
cd "$ROOT"
PY="$ROOT/scripts/pt"

RUN_DATE="${RUN_DATE:-$(date -u +%F)}"
if [[ -z "${REPORT_ROOT:-}" ]]; then
  REPORT_ROOT="$("$PY" -c 'from src.obs.stage1.io import get_reports_root; print(get_reports_root() / "obs" / "stage1")')"
fi
[[ "$REPORT_ROOT" = /* ]] || REPORT_ROOT="$ROOT/$REPORT_ROOT"

echo "=== Stage1 DAILY $(date -u +%FT%TZ) ==="
snapshot_rc=0
"$PY" scripts/obs/stage1_daily_snapshot.py --repo "${STAGE1_INPUT_ROOT:-$ROOT}" \
  --out-dir "$REPORT_ROOT" --fail-on-new-alerts || snapshot_rc=$?
# The snapshot writes its artifacts before returning the actionable-alert code.
if [[ "$snapshot_rc" != 0 && "$snapshot_rc" != 2 ]]; then
  exit "$snapshot_rc"
fi

"$PY" scripts/obs/stage1_report_index.py \
  --root "$REPORT_ROOT" --out "$REPORT_ROOT/index.json" --run-date "$RUN_DATE"
"$PY" scripts/obs/validate_stage1_index.py \
  --root "$REPORT_ROOT" --index "$REPORT_ROOT/index.json" --out "$REPORT_ROOT/validation.json" \
  --require "${RUN_DATE}_snapshot.md" --require "${RUN_DATE}_summary.json"

exit "$snapshot_rc"
