#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# Cursor-safe default: avoid sandbox-incompatible markers; keep output concise.
MARK_EXPR='not network and not external_tools'

# Ingress CLI smoke needs PYTHONPATH for subprocess imports (your proven patch behavior).
PY_FIX='PYTHONPATH="$(pwd)/src:$(pwd)"'

cat <<EOF
# Run these commands ONE BY ONE (each is a separate chunk):
# Chunk 1 (fast/high-signal)
pytest -q -ra -m "${MARK_EXPR}" tests/governance tests/ops --maxfail=1

# Chunk 2
${PY_FIX} python3 -m pytest -q -ra -m "${MARK_EXPR}" tests/ingress --maxfail=1

# Chunk 3
pytest -q -ra -m "${MARK_EXPR}" tests/data tests/exchange tests/risk tests/research --maxfail=1

# Chunk 4 (often heavier; run last)
pytest -q -ra -m "${MARK_EXPR}" tests/ai_orchestration tests/obs --maxfail=1
EOF
