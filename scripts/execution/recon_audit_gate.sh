#!/usr/bin/env bash
#
# Recon Audit Gate Wrapper
#
# Wraps show_recon_audit.py for common operator workflows.
#
# Usage:
#   ./recon_audit_gate.sh summary-text
#   ./recon_audit_gate.sh summary-json
#   ./recon_audit_gate.sh gate [--json <path>]
#
# Exit codes:
#   0: Success (or no findings in gate mode)
#   2: Findings present (gate mode only)
#   1: Error (invalid subcommand, script failure)
#
# Design:
# - SIM/PAPER only (no external APIs)
# - Deterministic (stable output)
# - Operator-friendly (clear subcommands)

set -euo pipefail

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CLI_TOOL="${SCRIPT_DIR}/show_recon_audit.py"

# Check if CLI tool exists
if [[ ! -f "${CLI_TOOL}" ]]; then
    echo "Error: show_recon_audit.py not found at ${CLI_TOOL}" >&2
    exit 1
fi

# Choose Python runner (prefer uv)
if [[ -n "${PT_RECON_PYTHON_RUNNER:-}" ]]; then
  read -r -a PY_RUN <<< "${PT_RECON_PYTHON_RUNNER}"
elif command -v uv >/dev/null 2>&1; then
  PY_RUN=(uv run python)
elif command -v python3 >/dev/null 2>&1; then
  PY_RUN=(python3)
elif command -v python >/dev/null 2>&1; then
  PY_RUN=(python)
else
  echo "ERROR: No Python interpreter found (need uv, python3, or python)." >&2
  exit 1
fi

# Parse subcommand
SUBCOMMAND="${1:-}"

if [[ -z "${SUBCOMMAND}" ]]; then
    echo "Usage: $(basename "$0") <subcommand> [options]" >&2
    echo "" >&2
    echo "Subcommands:" >&2
    echo "  summary-text   Show reconciliation summaries (text format)" >&2
    echo "  summary-json   Show reconciliation summaries (JSON format)" >&2
    echo "  gate           CI/CD gate mode (exit 2 if findings present)" >&2
    echo "" >&2
    echo "Options (gate mode):" >&2
    echo "  --json <path>  Load from JSON export" >&2
    echo "" >&2
    echo "Exit codes:" >&2
    echo "  0: Success (no findings in gate mode)" >&2
    echo "  2: Findings present (gate mode only, not an error!)" >&2
    echo "  1: Script error" >&2
    exit 1
fi

# Route to appropriate handler
case "${SUBCOMMAND}" in
    summary-text)
        # Text format (human-readable)
        "${PY_RUN[@]}" "$SCRIPT_DIR/show_recon_audit.py" summary
        ;;

    summary-json)
        # JSON format (machine-readable)
        "${PY_RUN[@]}" "$SCRIPT_DIR/show_recon_audit.py" summary --format json
        ;;

    gate)
        # Gate mode: exit 2 if findings present
        # Note: Exit 2 means "findings detected", not "error"
        # This is intentional for CI/CD gates
        shift  # Remove 'gate' from args
        "${PY_RUN[@]}" "$SCRIPT_DIR/show_recon_audit.py" summary --format json --exit-on-findings "$@"
        ;;

    *)
        echo "Error: Unknown subcommand '${SUBCOMMAND}'" >&2
        echo "Valid subcommands: summary-text, summary-json, gate" >&2
        exit 1
        ;;
esac
