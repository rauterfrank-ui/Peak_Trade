#!/usr/bin/env bash
# ============================================================================
# Peak_Trade Repo Cleanup Script
# ============================================================================
# Usage:
#   ./scripts/cleanup_repo.sh        # Safe cleanup (caches/build only)
#   ./scripts/cleanup_repo.sh --all  # Full cleanup (git clean -fdX)
#
# This script is idempotent: running it multiple times produces the same result.
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

echo "== Peak_Trade Cleanup =="
echo "Repo: $REPO_ROOT"
echo ""

# Track what we deleted
DELETED_COUNT=0

# Helper function for counting deletions
cleanup_dir() {
    local pattern="$1"
    local count
    count=$(find . -type d -name "$pattern" 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$count" -gt 0 ]]; then
        echo "  Removing $count $pattern directories..."
        find . -type d -name "$pattern" -exec rm -rf {} + 2>/dev/null || true
        DELETED_COUNT=$((DELETED_COUNT + count))
    fi
}

cleanup_file() {
    local pattern="$1"
    local count
    count=$(find . -name "$pattern" -type f 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$count" -gt 0 ]]; then
        echo "  Removing $count $pattern files..."
        find . -name "$pattern" -type f -delete 2>/dev/null || true
        DELETED_COUNT=$((DELETED_COUNT + count))
    fi
}

echo "[1/3] Cleaning Python caches..."
cleanup_dir "__pycache__"
cleanup_file "*.pyc"
cleanup_file "*.pyo"

echo "[2/3] Cleaning tool caches..."
cleanup_dir ".pytest_cache"
cleanup_dir ".mypy_cache"
cleanup_dir ".ruff_cache"
cleanup_dir ".tox"
cleanup_dir "*.egg-info"
cleanup_dir "htmlcov"
cleanup_file ".coverage"
cleanup_file ".DS_Store"

echo "[3/3] Cleaning build artifacts..."
if [[ -d "build" ]]; then
    echo "  Removing build/"
    rm -rf build/
    DELETED_COUNT=$((DELETED_COUNT + 1))
fi
if [[ -d "dist" ]]; then
    echo "  Removing dist/"
    rm -rf dist/
    DELETED_COUNT=$((DELETED_COUNT + 1))
fi

echo ""
echo "Safe cleanup complete. Removed $DELETED_COUNT items."

# Full cleanup mode
if [[ "${1:-}" == "--all" ]]; then
    echo ""
    echo "== Full Cleanup Mode (--all) =="
    echo "WARNING: This removes ALL gitignored files (data/, logs/, results/, etc.)"
    echo ""
    echo "Running: git clean -fdX"
    git clean -fdX
    echo ""
    echo "Full cleanup complete."
fi

echo ""
echo "== Status =="
git status -sb
