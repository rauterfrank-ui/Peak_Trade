#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

python3 "$ROOT_DIR/scripts/ops/check_markdown_links.py" \
  --root "$ROOT_DIR" \
  --paths README.md docs/ops docs/PEAK_TRADE_STATUS_OVERVIEW.md
