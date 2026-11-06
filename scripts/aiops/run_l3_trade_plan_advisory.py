#!/usr/bin/env python3
"""
CLI Script: L3 Trade Plan Advisory Runner (pointer-only, files-only, deterministic)

Runs L3 Trade Plan Advisory with pointer-only inputs; enforces files-only tooling.
NO live execution; no promotion; no learning writes.

Usage:
    python scripts/aiops/run_l3_trade_plan_advisory.py \\
        --input tests/fixtures/l3_pointer_only_input.json \\
        --out evidence_packs/L3_demo

Exit Codes:
    0: Success
    2: Validation error (pointer-only, SoD, tooling)
    3: Runtime error

Reference:
- config/capability_scopes/L3_trade_plan_advisory.toml
- docs/dev/RUNNER_INDEX.md (Tier A)
"""

import argparse
import json
import sys
from pathlib import Path

# Add repo root for src imports
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))

from src.ai_orchestration.l3_runner import (
    L3PointerOnlyViolation,
    L3Runner,
    L3RunnerError,
    L3ToolingViolation,
)


def main():
    parser = argparse.ArgumentParser(
        description="L3 Trade Plan Advisory Runner (pointer-only, files-only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run with pointer-only input JSON
  python scripts/aiops/run_l3_trade_plan_advisory.py \\
      --input tests/fixtures/l3_pointer_only_input.json \\
      --out evidence_packs/L3_demo

  # Minimal input (no artifacts)
  python scripts/aiops/run_l3_trade_plan_advisory.py \\
      --out evidence_packs/L3_minimal

Exit Codes:
  0: Success
  2: Validation error (pointer-only, SoD, tooling)
  3: Runtime error
        """,
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to pointer-only input JSON (FeatureView/EvidenceCapsule style). Default: minimal in-memory input.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory for run_manifest.json and operator_output.md (default: evidence_packs/L3_<timestamp>).",
    )
    parser.add_argument(
        "--mode",
        default="dry-run",
        help="Run mode (default: dry-run).",
    )
    args = parser.parse_args()

    # Load or build pointer-only input
    if args.input and args.input.exists():
        with open(args.input) as f:
            inputs = json.load(f)
    else:
        # Minimal pointer-only input for smoke/dry-run
        inputs = {"run_id": "l3-cli", "ts_ms": 0, "artifacts": []}

    try:
        runner = L3Runner()
        result = runner.run(
            inputs=inputs,
            mode=args.mode,
            out_dir=args.out,
        )
        print(result.summary)
        print("\nArtifacts:")
        for p in result.artifacts:
            print(f"  - {p}")
        return 0
    except L3PointerOnlyViolation as e:
        print(f"Validation error (pointer-only): {e}", file=sys.stderr)
        return 2
    except L3ToolingViolation as e:
        print(f"Validation error (tooling): {e}", file=sys.stderr)
        return 2
    except L3RunnerError as e:
        print(f"Runner error: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
