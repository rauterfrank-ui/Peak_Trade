#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Peak_Trade: Render Backtest Report (P1 Evidence Chain)
# ==============================================================================
#
# Renders a Quarto HTML report from evidence chain artifacts.
#
# Usage:
#   bash scripts/render_last_report.sh [run_id]
#
#   - Ohne run_id: wählt neuestes results/<run_id> (nach timestamp sortiert)
#   - Mit run_id: rendert spezifisches results/<run_id>
#
# Output:
#   results/<run_id>/report/backtest.html
#
# Graceful degradation:
#   - Wenn quarto nicht installiert: WARN + exit 0 (kein Fehler)
#   - Wenn run_id nicht existiert: ERROR + exit 1
#
# ==============================================================================

# Farb-Codes für Output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==============================================================================
# Funktionen
# ==============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

check_quarto() {
    if ! command -v quarto &> /dev/null; then
        log_warn "quarto is not installed or not in PATH"
        log_warn "Install quarto from https://quarto.org/docs/get-started/"
        log_warn "Skipping report rendering (graceful degradation)"
        return 1
    fi
    return 0
}

get_latest_run_id() {
    # Findet neuestes results/<run_id> nach mtime
    local latest_dir
    latest_dir=$(find results -mindepth 1 -maxdepth 1 -type d -print0 2>/dev/null \
        | xargs -0 ls -dt 2>/dev/null \
        | head -n 1)

    if [[ -z "$latest_dir" ]]; then
        log_error "No run directories found in results/"
        return 1
    fi

    basename "$latest_dir"
}

# ==============================================================================
# Main
# ==============================================================================

main() {
    local run_id="${1:-}"

    log_info "Peak_Trade Report Renderer (P1 Evidence Chain)"
    echo ""

    # Check quarto installation (graceful degradation)
    if ! check_quarto; then
        exit 0  # Exit 0 weil kein harter Fehler
    fi

    # Determine run_id
    if [[ -z "$run_id" ]]; then
        log_info "No run_id provided, selecting latest run..."
        run_id=$(get_latest_run_id) || exit 1
        log_info "Selected run_id: $run_id"
    fi

    # Validate run_dir exists
    local run_dir="results/$run_id"
    if [[ ! -d "$run_dir" ]]; then
        log_error "Run directory not found: $run_dir"
        exit 1
    fi

    log_info "Run directory: $run_dir"

    # Check for required artifacts
    local config_snapshot="$run_dir/config_snapshot.json"
    local stats_json="$run_dir/stats.json"
    local equity_csv="$run_dir/equity.csv"

    local missing_artifacts=()
    [[ ! -f "$config_snapshot" ]] && missing_artifacts+=("config_snapshot.json")
    [[ ! -f "$stats_json" ]] && missing_artifacts+=("stats.json")
    [[ ! -f "$equity_csv" ]] && missing_artifacts+=("equity.csv")

    if [[ ${#missing_artifacts[@]} -gt 0 ]]; then
        log_warn "Missing artifacts in $run_dir:"
        for artifact in "${missing_artifacts[@]}"; do
            log_warn "  - $artifact"
        done
        log_warn "Report may be incomplete, but continuing..."
    fi

    # Create report output directory
    local report_dir="$run_dir/report"
    mkdir -p "$report_dir"

    # Create _run symlink/copy for Quarto template
    local quarto_dir="reports/quarto"
    local quarto_run_link="$quarto_dir/_run"

    # Remove old symlink if exists
    if [[ -e "$quarto_run_link" ]] || [[ -L "$quarto_run_link" ]]; then
        rm -rf "$quarto_run_link"
    fi

    # Copy artifacts to _run (safer than symlink for Quarto)
    log_info "Copying artifacts to $quarto_run_link..."
    cp -r "$run_dir" "$quarto_run_link"

    # Render Quarto report
    log_info "Rendering Quarto report..."
    local qmd_template="$quarto_dir/backtest_report.qmd"
    local output_html="$report_dir/backtest.html"

    if [[ ! -f "$qmd_template" ]]; then
        log_error "Quarto template not found: $qmd_template"
        exit 1
    fi

    # Run quarto render
    if quarto render "$qmd_template" --output "$output_html" --quiet; then
        log_success "Report rendered: $output_html"
        echo ""
        log_info "Open in browser:"
        log_info "  open $output_html"
        echo ""
    else
        log_error "Quarto render failed"
        exit 1
    fi

    # Cleanup _run directory
    rm -rf "$quarto_run_link"

    exit 0
}

# ==============================================================================
# Entry Point
# ==============================================================================

main "$@"
