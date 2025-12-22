#!/usr/bin/env bash
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  echo "❌ uv not found. Install uv first."
  exit 1
fi

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

uv export --format requirements.txt \
  --all-extras --all-groups \
  --locked --no-hashes \
  -o "$tmp"

diff -u requirements.txt "$tmp"
echo "✅ requirements.txt matches uv.lock export."
