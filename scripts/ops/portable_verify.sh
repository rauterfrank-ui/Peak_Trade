#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

have() { command -v "$1" >/dev/null 2>&1; }

echo "[verify] python: $(python3 --version 2>/dev/null || true)"

echo "[verify] ruff: prefer CLI if runnable, else python3 -m ruff"
if have ruff && ruff --version >/dev/null 2>&1; then
  echo "[verify] using: ruff format --check"
  ruff format --check src tests scripts
else
  echo "[verify] using: python3 -m ruff format --check"
  python3 -m ruff format --check src tests scripts
fi

echo "[verify] pytest -> python3 -m pytest $*"
python3 -m pytest "$@"

echo "[hash] hashing (macOS portable) — only existing files passed as args"
FILES=()
for a in "$@"; do
  [[ "$a" == -* ]] && continue
  [[ -f "$a" ]] && FILES+=("$a")
done
if (( ${#FILES[@]} == 0 )); then
  echo "[hash] no files to hash (pass file paths as args; flags are ignored)"
  exit 0
fi
if have sha256sum; then
  sha256sum "${FILES[@]}"
else
  for f in "${FILES[@]}"; do
    shasum -a 256 "$f"
  done
fi
