#!/usr/bin/env bash
set -euo pipefail

F="docs/ops/README.md"
if [[ ! -f "$F" ]]; then
  echo "ERROR: missing $F"
  exit 1
fi

if rg -n -q '^# Test README\b' "$F"; then
  echo "ERROR: $F looks like a local fixture ('# Test README')."
  echo "Fix: git checkout origin/main -- $F (or restore from your branch HEAD)."
  exit 1
fi

if ! rg -n -q 'PR Inventory|pr_inventory' "$F"; then
  echo "ERROR: $F missing expected PR Inventory reference."
  exit 1
fi

echo "OK: $F looks sane."
