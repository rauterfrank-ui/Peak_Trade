#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

git config core.hooksPath .githooks
echo "[OK] core.hooksPath set to .githooks (repo-local)"
echo "Verify: $(git config core.hooksPath)"
