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
if [[ "${CODE}" -eq 2 ]]; then
  STATUS_LABEL="WARN"
  STATUS_CLASS="warn"
elif [[ "${CODE}" -ne 0 ]]; then
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
.badge.warn { border-color: #f59e0b66; background: #f59e0b22; }


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
# Use python to read file directly (more robust than pipe for large outputs)
python3 - <<'PY2' "$TMP" "$TS" "$CODE" "$OUT" "$JSON_OUT"
import json, sys
from pathlib import Path

tmp_file = sys.argv[1]
ts = sys.argv[2]
code = sys.argv[3]
html_path = sys.argv[4]
json_path = sys.argv[5]

try:
    output = Path(tmp_file).read_text(encoding='utf-8', errors='replace')
except Exception as e:
    output = f"Error reading output: {e}"

data = {
    "generated_at_utc": ts,
    "exit_code": int(code),
    "html_path": html_path,
    "json_path": json_path,
    "output": output
}

Path(json_path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
PY2

echo "✅ Wrote: $OUT (exit code: $CODE)"
exit 0
