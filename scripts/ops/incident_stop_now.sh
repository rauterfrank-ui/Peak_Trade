#!/usr/bin/env bash
set -euo pipefail

UTC_TS="$(date -u +"%Y%m%dT%H%M%SZ")"
INCIDENT_SLUG="${INCIDENT_SLUG:-manual-stop}"
OUT_DIR="out/ops/incident_stop_${UTC_TS}_${INCIDENT_SLUG}"
mkdir -p "$OUT_DIR"

STATE_FILE="${OUT_DIR}/incident_stop_state.env"
LOG_FILE="${OUT_DIR}/incident_stop_summary.md"

{
  echo "PT_INCIDENT_STOP=1"
  echo "PT_FORCE_NO_TRADE=1"
  echo "PT_ENABLED=0"
  echo "PT_ARMED=0"
  echo "INCIDENT_SLUG=${INCIDENT_SLUG}"
  echo "TIMESTAMP_UTC=${UTC_TS}"
} > "$STATE_FILE"

{
  echo "# Incident Stop Now"
  echo
  echo "- Timestamp (UTC): ${UTC_TS}"
  echo "- Incident slug: ${INCIDENT_SLUG}"
  echo "- Action: STOP NOW / FREEZE"
  echo "- Policy: NO_TRADE enforced"
  echo "- Enabled gate: 0"
  echo "- Armed gate: 0"
  echo
  echo "## Outputs"
  echo "- $(basename "$STATE_FILE")"
  echo
  echo "## Notes"
  echo "- No order placement performed"
  echo "- No exchange mutation performed"
  echo "- Use follow-up snapshot builder for evidence pack"
} > "$LOG_FILE"

echo "Incident stop evidence written to: ${OUT_DIR}"
echo "NO_TRADE enforced locally via evidence state file: ${STATE_FILE}"
