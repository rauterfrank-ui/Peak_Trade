#!/usr/bin/env bash
set -euo pipefail

MATRIX="docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md"
REGISTRY="config/model_registry.toml"

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
# This gate is not application runtime; skip the trading import preflight.
export PT_SKIP_TRADING_PREFLIGHT=1
"$ROOT/scripts/pt" src/governance/validate_ai_matrix_vs_registry.py "${MATRIX}" "${REGISTRY}"
echo "[PASS] AI matrix consistency gate"