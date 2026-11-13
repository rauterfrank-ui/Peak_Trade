#!/usr/bin/env bash
set -euo pipefail

output_dir="${OUT_DIR:-out/ops/p86_gate_${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}}"
mkdir -p "$output_dir"
cat > "$output_dir/P86_GATE_RESULT.json" <<'JSON'
{"overall_ok":false,"reason":"retired_readiness_chain"}
JSON
echo "P86_GATE_FAIL overall_ok=false reason=retired_readiness_chain"
exit 3
