#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-reports/ops/ops_doctor_dashboard.html}"
mkdir -p "$(dirname "$OUT")"

TMP="$(mktemp)"
CODE=0

# Capture doctor output (no assumptions about ANSI stripping; v0 = plain <pre>)
./scripts/ops/ops_center.sh doctor >"$TMP" 2>&1 || CODE=$?

TS="$(date -u +"%Y-%m-%d %H:%M:%S UTC")"

cat >"$OUT" <<HTML
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Ops Doctor Dashboard</title>
  <style>
    body { font-family: ui-sans-serif, system-ui, -apple-system; margin: 24px; }
    .card { border: 1px solid #3333; border-radius: 16px; padding: 16px; margin-bottom: 16px; }
    .kpi { font-size: 18px; font-weight: 700; }
    pre { white-space: pre-wrap; word-break: break-word; padding: 12px; border-radius: 12px; border: 1px solid #3333; }
  </style>
</head>
<body>
  <div class="card">
    <div class="kpi">Ops Doctor Dashboard (v0)</div>
    <div>Generated: ${TS}</div>
    <div>Exit code: ${CODE}</div>
  </div>

  <div class="card">
    <div class="kpi">Raw Output</div>
    <pre>$(sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g' "$TMP")</pre>
  </div>
</body>
</html>
HTML

echo "✅ Wrote: $OUT (exit code: $CODE)"
exit 0
