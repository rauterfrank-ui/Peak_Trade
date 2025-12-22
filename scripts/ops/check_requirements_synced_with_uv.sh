#!/usr/bin/env bash
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  echo "❌ uv not found. Install uv first."
  exit 1
fi

tmp="$(mktemp)"
tmp_normalized="$(mktemp)"
req_normalized="$(mktemp)"
trap 'rm -f "$tmp" "$tmp_normalized" "$req_normalized"' EXIT

uv export --format requirements.txt \
  --all-extras --all-groups \
  --locked --no-hashes \
  -o "$tmp"

# Normalize both files: remove the header comment line with the temp path
# (keep first line, skip second line with path, keep rest)
sed '2s|^#    uv export.*|#    uv export --format requirements.txt ...|' requirements.txt > "$req_normalized"
sed '2s|^#    uv export.*|#    uv export --format requirements.txt ...|' "$tmp" > "$tmp_normalized"

diff -u "$req_normalized" "$tmp_normalized"
echo "✅ requirements.txt matches uv.lock export."
