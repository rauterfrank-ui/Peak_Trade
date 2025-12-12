#!/usr/bin/env bash
set -euo pipefail

# install_desktop_shortcuts.sh
# Creates desktop symlinks for Peak_Trade TODO board (macOS)

DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help)
      cat <<'TXT'
install_desktop_shortcuts.sh

Creates desktop symlinks for quick access to TODO board and docs.

Usage:
  scripts/install_desktop_shortcuts.sh
  scripts/install_desktop_shortcuts.sh --dry-run

Options:
  --dry-run    Show what would be created without creating anything
  -h, --help   Show this help message

Creates:
  ~/Desktop/PEAK_TRADE_TODO_BOARD.html → docs/00_overview/PEAK_TRADE_TODO_BOARD.html
  ~/Desktop/Peak_Trade_Docs_Overview   → docs/00_overview
TXT
      exit 0
      ;;
    *) echo "Unknown arg: $arg" >&2; exit 2 ;;
  esac
done

# Detect repo root
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# Desktop path (macOS)
DESKTOP="$HOME/Desktop"
if [[ ! -d "$DESKTOP" ]]; then
  echo "❌ Desktop directory not found: $DESKTOP"
  echo "   This script is designed for macOS systems."
  exit 1
fi

# Target paths
TODO_HTML="$REPO_ROOT/docs/00_overview/PEAK_TRADE_TODO_BOARD.html"
OVERVIEW_DIR="$REPO_ROOT/docs/00_overview"

# Verify targets exist
if [[ ! -f "$TODO_HTML" ]]; then
  echo "⚠️  TODO board HTML not found: $TODO_HTML"
  echo "   Run: python3 scripts/build_todo_board_html.py"
  exit 1
fi

if [[ ! -d "$OVERVIEW_DIR" ]]; then
  echo "❌ Overview directory not found: $OVERVIEW_DIR"
  exit 1
fi

# Symlink paths
LINK_TODO="$DESKTOP/PEAK_TRADE_TODO_BOARD.html"
LINK_OVERVIEW="$DESKTOP/Peak_Trade_Docs_Overview"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "== Dry Run Mode =="
  echo "Would create:"
  echo "  $LINK_TODO"
  echo "    → $TODO_HTML"
  echo "  $LINK_OVERVIEW"
  echo "    → $OVERVIEW_DIR"
  exit 0
fi

# Create symlinks (idempotent with -f)
echo "Creating desktop shortcuts..."
ln -sfn "$TODO_HTML" "$LINK_TODO"
echo "✓ $LINK_TODO"

ln -sfn "$OVERVIEW_DIR" "$LINK_OVERVIEW"
echo "✓ $LINK_OVERVIEW"

echo ""
echo "✅ OK - Desktop shortcuts created"
echo "   Double-click icons on Desktop to access TODO board and docs"

exit 0
