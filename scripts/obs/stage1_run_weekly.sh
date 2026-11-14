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

mkdir -p "$REPORT_ROOT"
draft="$(mktemp "$REPORT_ROOT/.trend-XXXXXX")"
trap 'rm -f "$draft"' EXIT
"$PY" scripts/obs/stage1_trend_report.py --dir "$REPORT_ROOT" --days 14 > "$draft"
OUT="$REPORT_ROOT/${RUN_DATE}_trend.md"
mv "$draft" "$OUT"

"$PY" scripts/obs/stage1_report_index.py \
  --root "$REPORT_ROOT" --out "$REPORT_ROOT/index.json" --run-date "$RUN_DATE"
"$PY" scripts/obs/validate_stage1_index.py \
  --root "$REPORT_ROOT" --index "$REPORT_ROOT/index.json" --out "$REPORT_ROOT/validation.json" \
  --require "${RUN_DATE}_trend.md" --require "stage1_trend.json"
