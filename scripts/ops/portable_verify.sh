#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

have() { command -v "$1" >/dev/null 2>&1; }

FIX=0
NO_RUFF=0
PYTEST_ARGS=()

usage() {
  cat <<USAGE
Usage:
  portable_verify.sh [--fix] [--no-ruff] [pytest args...]

Behavior:
  - Ruff gate:
      default: run "format --check"
      --fix: run "format" (applies formatting)
      --no-ruff: skip ruff entirely
    Ruff invocation is "ruff" if runnable; else "python3 -m ruff".
  - Pytest:
      always runs "python3 -m pytest <pytest args...>"
  - Hash:
      hashes only existing file paths passed among pytest args (flags ignored).
USAGE
}

# Parse our flags; everything else is forwarded to pytest
while (( $# )); do
  case "$1" in
    --fix) FIX=1; shift ;;
    --no-ruff) NO_RUFF=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) PYTEST_ARGS+=("$1"); shift ;;
  esac
done

echo "[verify] python: $(python3 --version 2>/dev/null || true)"

# Select ruff command
RUFF_CMD=("python3" "-m" "ruff")
if have ruff && ruff --version >/dev/null 2>&1; then
  RUFF_CMD=("ruff")
fi
echo "[verify] ruff cmd: ${RUFF_CMD[*]}"

if (( NO_RUFF )); then
  echo "[verify] ruff: skipped (--no-ruff)"
else
  if (( FIX )); then
    echo "[verify] ruff: applying formatting (--fix)"
    "${RUFF_CMD[@]}" format src tests scripts
  else
    echo "[verify] ruff: checking formatting"
    "${RUFF_CMD[@]}" format --check src tests scripts
  fi
fi

echo "[verify] pytest -> python3 -m pytest ${PYTEST_ARGS[*]:-}"
python3 -m pytest "${PYTEST_ARGS[@]}"

echo "[hash] hashing (macOS portable) — only existing files among pytest args"
FILES=()
for a in "${PYTEST_ARGS[@]}"; do
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
