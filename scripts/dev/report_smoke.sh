#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# report_smoke.sh
# Renders the Quarto smoke report (minimal HTML self-contained)
# -----------------------------------------------------------------------------
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "${REPO_ROOT}"

SMOKE_QMD="templates/quarto/smoke.qmd"
OUTPUT_DIR="reports/quarto"
OUTPUT_FILE="${OUTPUT_DIR}/smoke.html"

echo "=== Quarto Smoke Report ==="
echo "Input:  ${SMOKE_QMD}"
echo "Output: ${OUTPUT_FILE}"
echo ""

if [ ! -f "${SMOKE_QMD}" ]; then
  echo "ERROR: ${SMOKE_QMD} not found"
  exit 1
fi

# Create output directory if needed
mkdir -p "${OUTPUT_DIR}"

# Render with Quarto (creates smoke.html in templates/quarto/)
cd templates/quarto
quarto render smoke.qmd --to html

# Move output to reports/
cd "${REPO_ROOT}"
mv templates/quarto/smoke.html "${OUTPUT_FILE}"

echo ""
echo "✓ Smoke report rendered successfully"
echo "  Output: ${OUTPUT_FILE}"
