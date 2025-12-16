#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/run_portfolio_mtf_integration.sh [options]

Options:
  --symbols "BTCUSDT ETHUSDT"   Symbols passed to scripts/run_portfolio_mtf_example.py (default: "BTCUSDT ETHUSDT")
  --periods 100                 Periods passed to example script (default: 100)
  --pytest-args "-q"            Extra args for pytest (default: "-v")
  --search-dirs "results reports"
                                Space-separated dirs (relative to repo root) to search for stats/equity (default: "results reports")
  --skip-tests                  Skip pytest
  --skip-example                Skip example script
  -h, --help                    Show help

Examples:
  scripts/run_portfolio_mtf_integration.sh
  scripts/run_portfolio_mtf_integration.sh --symbols "BTCUSDT ETHUSDT" --periods 200
  scripts/run_portfolio_mtf_integration.sh --skip-tests
  scripts/run_portfolio_mtf_integration.sh --skip-example
EOF
}

log() { printf "\n==> %s\n" "$*"; }
warn() { printf "\n[WARN] %s\n" "$*" >&2; }
die() { printf "\n[FAIL] %s\n" "$*" >&2; exit 1; }

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -n "$REPO_ROOT" ]] || die "Not inside a git repo. Please run from within your Peak_Trade repository."

SYMBOLS="BTCUSDT ETHUSDT"
PERIODS="100"
PYTEST_ARGS="-v"
SEARCH_DIRS="results reports"
SKIP_TESTS="0"
SKIP_EXAMPLE="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --symbols) SYMBOLS="${2:-}"; shift 2;;
    --periods) PERIODS="${2:-}"; shift 2;;
    --pytest-args) PYTEST_ARGS="${2:-}"; shift 2;;
    --search-dirs) SEARCH_DIRS="${2:-}"; shift 2;;
    --skip-tests) SKIP_TESTS="1"; shift;;
    --skip-example) SKIP_EXAMPLE="1"; shift;;
    -h|--help) usage; exit 0;;
    *) die "Unknown arg: $1 (use --help)";;
  esac
done

cd "$REPO_ROOT"

log "Run meta (traceability)…"
log "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ) (UTC)"
if command -v git >/dev/null 2>&1; then
  log "Git: $(git rev-parse --short HEAD 2>/dev/null || echo n/a)  branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo n/a)"
fi
log "Python: $(python -c "import sys; print(sys.version.replace('\n', ' '))" 2>/dev/null || echo n/a)"

command -v python >/dev/null 2>&1 || die "python not found in PATH"

if [[ "$SKIP_TESTS" == "0" ]]; then
  log "Running targeted pytest suite…"
  python -m pytest tests/test_portfolio_mtf_align.py tests/test_portfolio_cash_rounding.py ${PYTEST_ARGS}
else
  warn "Skipping tests (--skip-tests)."
fi

EXAMPLE="scripts/run_portfolio_mtf_example.py"
if [[ "$SKIP_EXAMPLE" == "0" ]]; then
  [[ -f "$EXAMPLE" ]] || die "Example script not found: $EXAMPLE"
  log "Running example…"
  # shellcheck disable=SC2086
  python "$EXAMPLE" --symbols ${SYMBOLS} --periods "${PERIODS}"
else
  warn "Skipping example (--skip-example)."
fi

newest_file_in_dirs() {
  local filename="$1"
  shift
  local -a dirs=("$@")
  local -a candidates=()

  for d in "${dirs[@]}"; do
    local path="$REPO_ROOT/$d"
    [[ -d "$path" ]] || continue
    while IFS= read -r -d '' f; do
      candidates+=("$f")
    done < <(find "$path" -type f -name "$filename" -print0 2>/dev/null || true)
  done

  if [[ ${#candidates[@]} -eq 0 ]]; then
    echo ""
    return 0
  fi

  local newest
  newest="$(ls -1t "${candidates[@]}" 2>/dev/null | head -n 1 || true)"
  echo "$newest"
}

read -r -a SEARCH_DIR_ARR <<<"$SEARCH_DIRS"

log "Searching newest outputs in: ${SEARCH_DIRS}"
STATS_PATH="$(newest_file_in_dirs "stats.json" "${SEARCH_DIR_ARR[@]}")"
EQUITY_PATH="$(newest_file_in_dirs "equity.csv" "${SEARCH_DIR_ARR[@]}")"

if [[ -z "$STATS_PATH" && -z "$EQUITY_PATH" ]]; then
  warn "No stats.json / equity.csv found in ${SEARCH_DIRS}."
  warn "If your example writes elsewhere, rerun with e.g.: --search-dirs \"results reports output\""
  # Best-effort hints (last few candidate files)
  for d in "${SEARCH_DIR_ARR[@]}"; do
    p="$REPO_ROOT/$d"
    [[ -d "$p" ]] || continue
    warn "Hints in ${d}/ (most recent files):"
    (find "$p" -type f \( -name "*.json" -o -name "*.csv" \) -print0 2>/dev/null | xargs -0 ls -1t 2>/dev/null | head -n 5) || true
  done
  exit 0
fi

if [[ -n "$STATS_PATH" ]]; then
  log "Newest stats.json: ${STATS_PATH#$REPO_ROOT/}"
  if command -v jq >/dev/null 2>&1; then
    jq '.' "$STATS_PATH" || cat "$STATS_PATH"
  else
    cat "$STATS_PATH"
  fi
else
  warn "stats.json not found."
fi

if [[ -n "$EQUITY_PATH" ]]; then
  log "Newest equity.csv: ${EQUITY_PATH#$REPO_ROOT/}"
  head -n 20 "$EQUITY_PATH"
else
  warn "equity.csv not found."
fi

log "Done."
