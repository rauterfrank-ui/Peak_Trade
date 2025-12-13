#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "== TODO Board Guard =="

echo "[1/4] Run generator twice (idempotency)"
python3 scripts/build_todo_board_html.py
python3 scripts/build_todo_board_html.py

echo "[2/4] Ensure working tree stays clean (no diffs)"
if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: Working tree is dirty after generator run."
  git status --porcelain
  echo
  echo "Diff:"
  git --no-pager diff
  exit 1
fi

echo "[3/4] Smoke tests"
python3 -m pytest tests/test_todo_board_parser_smoke.py -q

echo "[4/4] Idempotency regression test"
python3 -m pytest tests/test_todo_board_idempotency.py -q

echo "OK: TODO board is deterministic, leak-safe, and diff-zero."
