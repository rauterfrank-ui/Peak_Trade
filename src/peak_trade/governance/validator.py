"""CLI wrapper for AI matrix vs registry validator (P0–P2). Delegates to src/governance/validate_ai_matrix_vs_registry.py."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Default paths relative to repo root (caller expected to run from repo root)
DEFAULT_MATRIX = "docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md"
DEFAULT_REGISTRY = "config/model_registry.toml"


def _parse(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="peak_trade.governance.validator")
    p.add_argument(
        "--level",
        choices=["P0", "P1", "P2"],
        default="P2",
        help="Validation strictness level.",
    )
    p.add_argument(
        "--matrix",
        type=Path,
        default=None,
        help="Path to AI autonomy matrix (optional; uses repo default if omitted).",
    )
    p.add_argument(
        "--registry",
        type=Path,
        default=None,
        help="Path to model registry (optional; uses repo default if omitted).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse(argv)
    # script: src/governance/validate_ai_matrix_vs_registry.py; repo_root: parent of src
    src_dir = Path(__file__).resolve().parent.parent.parent
    repo_root = src_dir.parent
    script = src_dir / "governance" / "validate_ai_matrix_vs_registry.py"
    if not script.exists():
        print(f"Validator script not found: {script}", file=sys.stderr)
        return 1
    cmd = [sys.executable, str(script), "--level", ns.level]
    if ns.matrix is not None:
        cmd.append(str(ns.matrix))
    if ns.registry is not None:
        cmd.append(str(ns.registry))
    return subprocess.call(cmd, cwd=repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
