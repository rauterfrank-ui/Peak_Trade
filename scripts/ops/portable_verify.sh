#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

have() { command -v "$1" >/dev/null 2>&1; }

echo "[verify] python: $(python3 --version 2>/dev/null || true)"

if have ruff; then
  echo "[verify] ruff in PATH -> ruff format --check"
  ruff format --check src tests scripts
else
  echo "[verify] ruff not in PATH -> python3 -m ruff format --check"
  python3 -m ruff format --check src tests scripts
fi

echo "[verify] pytest -> python3 -m pytest $*"
python3 -m pytest "$@"

echo "[hash] hashing (macOS portable)"
if have sha256sum; then
  sha256sum "$@"
else
  # macOS
  for f in "$@"; do
    shasum -a 256 "$f"
  done
fi
