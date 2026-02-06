#!/usr/bin/env bash
set -euo pipefail

MATRIX="docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md"
REGISTRY="config/model_registry.toml"

python3 src/governance/validate_ai_matrix_vs_registry.py "${MATRIX}" "${REGISTRY}"
echo "[PASS] AI matrix consistency gate"
