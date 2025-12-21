#!/usr/bin/env bash
set -euo pipefail

cd "$HOME/Peak_Trade"

# Prefer project venv if present
if [ -f ".venv/bin/activate" ]; then
  source ".venv/bin/activate"
  PY="python"
else
  PY="python3"
fi

DATE="$(date +%F)"
mkdir -p "logs/obs/stage1"

echo "=== Stage1 DAILY $(date -Iseconds) ==="
"$PY" "scripts/obs/stage1_daily_snapshot.py" --fail-on-new-alerts
echo "=== done ==="
