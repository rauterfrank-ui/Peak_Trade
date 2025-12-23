#!/usr/bin/env bash
set -euo pipefail

# Peak_Trade Ops Doctor – Repository Health Check
# ================================================
# Führt umfassende Gesundheitschecks für das Repository durch.
#
# Usage:
#   ./scripts/ops/ops_doctor.sh                    # Alle Checks
#   ./scripts/ops/ops_doctor.sh --json             # JSON-Output
#   ./scripts/ops/ops_doctor.sh --check repo.git_root --check deps.uv_lock

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Nur Header ausgeben wenn NICHT im JSON-Modus
if [[ ! "$*" =~ --json ]]; then
    echo "🏥 Peak_Trade Ops Doctor"
    echo "Repository: ${REPO_ROOT}"
    echo ""
fi

cd "${REPO_ROOT}"

# Führe Python-Doctor aus
# Versuche python3, falls python nicht verfügbar
if command -v python3 &> /dev/null; then
    python3 -m src.ops.doctor "$@"
elif command -v python &> /dev/null; then
    python -m src.ops.doctor "$@"
else
    echo "❌ Error: Neither python nor python3 found in PATH" >&2
    exit 1
fi
