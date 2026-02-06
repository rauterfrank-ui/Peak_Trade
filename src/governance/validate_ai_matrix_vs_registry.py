#!/usr/bin/env python3
"""
Validate that the AI autonomy matrix path exists and model_registry.toml references it.
Used by scripts/governance/ai_matrix_consistency_gate.sh (fail-closed).
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: validate_ai_matrix_vs_registry.py <matrix_path> <registry_path>", file=sys.stderr)
        return 2
    matrix_path = Path(sys.argv[1])
    registry_path = Path(sys.argv[2])

    if not matrix_path.exists():
        print(f"Gate FAIL: matrix file not found: {matrix_path}", file=sys.stderr)
        return 1
    if not registry_path.exists():
        print(f"Gate FAIL: registry file not found: {registry_path}", file=sys.stderr)
        return 1

    ref_needle = "matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX"
    registry_text = registry_path.read_text()
    if ref_needle not in registry_text:
        print(
            f"Gate FAIL: {registry_path} must reference authoritative matrix "
            f"(e.g. Reference: docs/governance/{ref_needle}.md)",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
