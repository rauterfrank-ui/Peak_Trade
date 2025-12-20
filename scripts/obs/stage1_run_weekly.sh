#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/Peak_Trade"

if [ -f ".venv/bin/activate" ]; then
  source ".venv/bin/activate"
  PY="python"
else
  PY="python3"
fi

DATE="$(date +%F)"
OUT="reports/obs/stage1/${DATE}_trend.md"

echo "=== Stage1 WEEKLY $(date -Iseconds) ===" > "$OUT"
"$PY" "scripts/obs/stage1_trend_report.py" --days 14 >> "$OUT"
echo "=== wrote: $OUT ==="
