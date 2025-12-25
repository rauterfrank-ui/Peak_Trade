#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-reports/ops/ops_doctor_dashboard.html}"
JSON_OUT="${OUT%.html}.json"

mkdir -p "$(dirname "$OUT")"

TMP="$(mktemp)"
CODE=0

# Capture doctor output (no assumptions about ANSI stripping; v0 = plain <pre>)
./scripts/ops/ops_center.sh doctor >"$TMP" 2>&1 || CODE=$?

TS="$(date -u +"%Y-%m-%d %H:%M:%S UTC")"

STATUS_LABEL="PASS"
STATUS_CLASS="pass"
if [[ "${CODE}" -ne 0 ]]; then
  STATUS_LABEL="FAIL"
  STATUS_CLASS="fail"
fi


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
.row { display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
.badge { display:inline-block; padding: 4px 10px; border-radius: 999px; font-weight: 800; letter-spacing: .02em; border: 1px solid #3333; }
.badge.pass { border-color: #16a34a66; background: #16a34a22; }
.badge.fail { border-color: #dc262666; background: #dc262622; }

  </style>
</head>
<body>
  <div class="card">
    <div class="row"><div class="kpi">Ops Doctor Dashboard (v1)</div><div class="badge ${STATUS_CLASS}">${STATUS_LABEL}</div></div>
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


# JSON export (minimal; useful for tooling)
# Fields: generated_at_utc, exit_code, html_path, json_path, output
RAW_OUT="$(cat "$TMP")"
ESC_OUT="$(printf "%s" "$RAW_OUT" | python3 - <<'PY2'
import json,sys
print(json.dumps(sys.stdin.read()))
PY2
)"
cat >"$JSON_OUT" <<JSON
{
  "generated_at_utc": "${TS}",
  "exit_code": ${CODE},
  "html_path": "${OUT}",
  "json_path": "${JSON_OUT}",
  "output": ${ESC_OUT}
}
JSON

echo "✅ Wrote: $OUT (exit code: $CODE)"
exit 0
