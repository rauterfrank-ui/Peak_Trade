#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# Expect user has otel extras installed in their venv
python3 -c "import opentelemetry" >/dev/null 2>&1 || {
  echo "❌ OpenTelemetry deps missing. Install with: pip install -e '.[otel]'" >&2
  exit 1
}

export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
export OTEL_SERVICE_NAME="peak_trade_smoke_sender"

python3 scripts/obs/smoke_sender.py

echo ""
echo "Now open Grafana -> Explore -> Tempo and search for service: peak_trade_smoke_sender"
echo ""
