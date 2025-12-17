#!/usr/bin/env bash
# ============================================================================
# Peak Trade - Smoke Test Report Generator
# ============================================================================
# Renders a minimal Quarto smoke report to validate reporting infrastructure.
#
# Usage:
#   ./scripts/dev/report_smoke.sh           # Generate report
#   ./scripts/dev/report_smoke.sh --open    # Generate and open in browser
#
# Output:
#   reports/quarto/_smoke/smoke.html

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SMOKE_QMD="${REPO_ROOT}/reports/quarto/smoke.qmd"
OUTPUT_DIR="${REPO_ROOT}/reports/quarto/_smoke"
OUTPUT_HTML="${OUTPUT_DIR}/smoke.html"
FALLBACK_QMD="${OUTPUT_DIR}/_smoke_report.qmd"

OPEN_BROWSER=false

# ============================================================================
# Parse Arguments
# ============================================================================

while [[ $# -gt 0 ]]; do
  case $1 in
    --open)
      OPEN_BROWSER=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--open]"
      exit 1
      ;;
  esac
done

# ============================================================================
# Check Quarto Installation
# ============================================================================

if ! command -v quarto >/dev/null 2>&1; then
  echo ""
  echo "ERROR: Quarto not found."
  echo ""
  echo "Install with:"
  echo "  macOS:  brew install quarto"
  echo "  Other:  https://quarto.org/docs/get-started/"
  echo ""
  exit 1
fi

# ============================================================================
# Prepare Source Document
# ============================================================================

mkdir -p "${OUTPUT_DIR}"

if [[ -f "${SMOKE_QMD}" ]]; then
  # Use committed smoke report (preferred)
  SOURCE_QMD="${SMOKE_QMD}"
  echo "Using committed smoke report: ${SMOKE_QMD}"
else
  # Fallback: create minimal report on-the-fly
  SOURCE_QMD="${FALLBACK_QMD}"
  echo "Warning: ${SMOKE_QMD} not found. Creating fallback report."

  cat > "${FALLBACK_QMD}" <<'EOF'
---
title: "Peak Trade - Smoke Test Report (Fallback)"
format:
  html:
    embed-resources: true
    theme: cosmo
---

## Status

**Fallback smoke report generated.**

The committed smoke report was not found in this branch.

Expected location: `reports/quarto/smoke.qmd`

---

*Generated: `r format(Sys.time(), '%Y-%m-%d %H:%M:%S %Z')`*
EOF
fi

# ============================================================================
# Render Report
# ============================================================================

echo ""
echo "Rendering Quarto smoke report..."
echo ""

quarto render "${SOURCE_QMD}" --output-dir "${OUTPUT_DIR}"

# Ensure output file exists
if [[ ! -f "${OUTPUT_HTML}" ]]; then
  echo ""
  echo "ERROR: Report generation failed. Output not found: ${OUTPUT_HTML}"
  exit 1
fi

echo ""
echo "✓ Report generated: ${OUTPUT_HTML}"
echo ""

# ============================================================================
# Open in Browser (Optional)
# ============================================================================

if [[ "${OPEN_BROWSER}" == "true" ]]; then
  echo "Opening report in browser..."

  if command -v open >/dev/null 2>&1; then
    # macOS
    open "${OUTPUT_HTML}"
  elif command -v xdg-open >/dev/null 2>&1; then
    # Linux
    xdg-open "${OUTPUT_HTML}" 2>/dev/null &
  else
    echo ""
    echo "Note: Could not auto-open browser. Please open manually:"
    echo "  ${OUTPUT_HTML}"
    echo ""
  fi
fi

exit 0
