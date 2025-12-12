#!/usr/bin/env bash
set -euo pipefail

# open_todo_board.sh
# One-command TODO board: preflight → build → open

INSTALL_SHORTCUTS=0
JSON_MODE=0

for arg in "$@"; do
  case "$arg" in
    --install-shortcuts) INSTALL_SHORTCUTS=1 ;;
    --json) JSON_MODE=1 ;;
    -h|--help)
      cat <<'TXT'
open_todo_board.sh

One-command TODO board launch: checks status, builds, and opens.

Usage:
  scripts/open_todo_board.sh
  scripts/open_todo_board.sh --install-shortcuts
  scripts/open_todo_board.sh --json

Options:
  --install-shortcuts  Install desktop shortcuts before opening
  --json               Output results as JSON
  -h, --help           Show this help message

Steps:
  1. Run preflight check (if available)
  2. Build TODO board HTML
  3. Open in default browser (macOS)
TXT
      exit 0
      ;;
    *) echo "Unknown arg: $arg" >&2; exit 2 ;;
  esac
done

# Detect repo root
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# JSON output tracking
STEPS_JSON="[]"
ALL_OK=1

run_step() {
  local name="$1"
  local cmd="$2"
  local optional="${3:-0}"

  if [[ "$JSON_MODE" -eq 1 ]]; then
    if eval "$cmd" >/dev/null 2>&1; then
      STEPS_JSON=$(echo "$STEPS_JSON" | python3 -c "import sys, json; d=json.load(sys.stdin); d.append({'step':'$name','status':'ok'}); print(json.dumps(d))")
    else
      if [[ "$optional" -eq 1 ]]; then
        STEPS_JSON=$(echo "$STEPS_JSON" | python3 -c "import sys, json; d=json.load(sys.stdin); d.append({'step':'$name','status':'skipped'}); print(json.dumps(d))")
      else
        STEPS_JSON=$(echo "$STEPS_JSON" | python3 -c "import sys, json; d=json.load(sys.stdin); d.append({'step':'$name','status':'fail'}); print(json.dumps(d))")
        ALL_OK=0
      fi
    fi
  else
    echo "== $name =="
    if eval "$cmd"; then
      echo "✓ OK"
    else
      if [[ "$optional" -eq 1 ]]; then
        echo "ℹ️  Skipped (optional)"
      else
        echo "❌ Failed"
        ALL_OK=0
      fi
    fi
    echo
  fi
}

# Step 1: Install shortcuts (if requested)
if [[ "$INSTALL_SHORTCUTS" -eq 1 ]]; then
  run_step "install_shortcuts" "bash scripts/install_desktop_shortcuts.sh" 1
fi

# Step 2: Preflight check (optional)
if [[ -f "scripts/check_claude_code_ready.sh" ]]; then
  run_step "preflight_check" "bash scripts/check_claude_code_ready.sh || true" 1
fi

# Step 3: Build TODO board
run_step "build_todo_board" "python3 scripts/build_todo_board_html.py"

# Step 4: Open in browser (macOS)
TODO_HTML="docs/00_overview/PEAK_TRADE_TODO_BOARD.html"
if command -v open >/dev/null 2>&1; then
  run_step "open_browser" "open '$TODO_HTML'" 1
else
  if [[ "$JSON_MODE" -eq 1 ]]; then
    STEPS_JSON=$(echo "$STEPS_JSON" | python3 -c "import sys, json; d=json.load(sys.stdin); d.append({'step':'open_browser','status':'not_available'}); print(json.dumps(d))")
  else
    echo "== open_browser =="
    echo "ℹ️  'open' command not available (non-macOS system)"
    echo "   Manually open: $TODO_HTML"
    echo
  fi
fi

# Output results
if [[ "$JSON_MODE" -eq 1 ]]; then
  echo "{\"steps\":$STEPS_JSON,\"ok\":$([ "$ALL_OK" -eq 1 ] && echo 'true' || echo 'false')}"
else
  if [[ "$ALL_OK" -eq 1 ]]; then
    echo "✅ All steps completed successfully"
  else
    echo "⚠️  Some steps failed (see output above)"
  fi
fi

exit $((1 - ALL_OK))
